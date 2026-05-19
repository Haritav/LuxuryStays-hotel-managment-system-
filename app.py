from flask import Flask, render_template, request, redirect, url_for, session, flash
from decimal import Decimal, ROUND_HALF_UP
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import pymysql
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Harita*123",
        database="luxurystays"
    )

@app.route('/')
def search_form():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT hotel_id, city FROM hotels WHERE is_active = TRUE;")
        hotels = cursor.fetchall()
        return render_template('project.html', hotels=hotels)
    except Exception as e:
        print(f"Database error in search_form: {e}")
        return render_template('project.html', hotels=[])
    finally:
        cursor.close()
        conn.close()

@app.route('/search/results', methods=['POST'])
def search_results():
    hotel_id = request.form['hotel_id']
    check_in = request.form['check_in']
    check_out = request.form['check_out']
    guests = int(request.form['guests'])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Debug: Print received form data
        print(f"Search parameters - Hotel: {hotel_id}, Check-in: {check_in}, Check-out: {check_out}, Guests: {guests}")

        # Get hotel details
        cursor.execute("SELECT name FROM hotels WHERE hotel_id = %s", (hotel_id,))
        hotel = cursor.fetchone()
        
        # IMPORTANT: Consume all results before next query
        cursor.fetchall()  # This ensures no unread results remain
        
        if not hotel:
            print("No hotel found with ID:", hotel_id)
            return render_template('results.html', rooms=[], check_in=check_in, check_out=check_out)

        # Simplified query to find matching room types
        query = """
            SELECT 
                rt.room_type_id,
                rt.name AS room_name,
                rt.base_price,
                rt.max_occupancy,
                rt.description,
                (SELECT image_url FROM hotel_images 
                 WHERE hotel_id = %s AND is_primary = TRUE LIMIT 1) AS image_url
            FROM 
                room_types rt
            WHERE 
                rt.hotel_id = %s 
                AND rt.max_occupancy >= %s
        """
        
        cursor.execute(query, (hotel_id, hotel_id, guests))
        rooms = cursor.fetchall()
        
        # Debug output
        print(f"Found {len(rooms)} room types for hotel {hotel_id}")
        for room in rooms:
            print(room)

        return render_template('results.html', 
                            rooms=rooms, 
                            check_in=check_in, 
                            check_out=check_out,
                            hotel_name=hotel['name'])

    except Exception as e:
        print(f"Database error in search_results: {e}")
        return render_template('results.html', rooms=[], check_in=check_in, check_out=check_out)
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()
            
            if account:
                if check_password_hash(account['password_hash'], password):
                    session['loggedin'] = True
                    session['user_id'] = account['user_id']
                    session['email'] = account['email']
                    session['first_name'] = account['first_name']
                    session['last_name'] = account['last_name']
                    
                    cursor.execute('UPDATE users SET last_login = NOW() WHERE user_id = %s', 
                                 (account['user_id'],))
                    conn.commit()
                    
                    flash('Logged in successfully!', 'success')
                    
                    # Check if there's a redirect target in session (from attempted booking)
                    if 'booking_redirect' in session:
                        redirect_data = session.pop('booking_redirect')
                        return redirect(url_for('booking_confirmation',
                                            room_type_id=redirect_data['room_type_id'],
                                            check_in=redirect_data['check_in'],
                                            check_out=redirect_data['check_out']))
                    
                    # If no specific booking, redirect to home page instead of dashboard
                    return redirect(url_for('search_form'))
                    
                else:
                    flash('Incorrect password!', 'danger')
            else:
                flash('Email address not found!', 'danger')
                
        except Exception as e:
            print(f"Database error in login: {e}")
            flash('An error occurred during login', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove session data
    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('email', None)
    session.pop('first_name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get user details
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (session['user_id'],))
            account = cursor.fetchone()
            
            # Get user's bookings
            cursor.execute('''
                SELECT b.*, h.name as hotel_name, h.city, h.country 
                FROM bookings b
                JOIN hotels h ON b.hotel_id = h.hotel_id
                WHERE b.user_id = %s
                ORDER BY b.check_in_date DESC
                LIMIT 3
            ''', (session['user_id'],))
            bookings = cursor.fetchall()
            
            # Get featured hotels
            cursor.execute('''
                SELECT h.*, hi.image_url 
                FROM hotels h
                LEFT JOIN hotel_images hi ON h.hotel_id = hi.hotel_id AND hi.is_primary = TRUE
                WHERE h.is_active = TRUE
                ORDER BY h.star_rating DESC
                LIMIT 4
            ''')
            featured_hotels = cursor.fetchall()
            
            return render_template('dashboard.html',
                                account=account,
                                bookings=bookings,
                                featured_hotels=featured_hotels)
            
        except Error as e:
            print(f"Database error in dashboard: {e}")
            flash('An error occurred while loading dashboard', 'danger')
            return redirect(url_for('login'))
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
     
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate form data
        if not all([first_name, last_name, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Connect to database
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                
                # Check if email already exists
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    flash('Email already registered', 'error')
                    return redirect(url_for('register'))
                
                # Insert new user
                cursor.execute("""
                    INSERT INTO users (first_name, last_name, email, password_hash, registration_date)VALUES (%s, %s, %s, %s, NOW())
                """, (first_name, last_name, email, hashed_password))
                
                connection.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))  # Assuming you have a login route
                
            except Error as e:
                connection.rollback()
                flash('An error occurred during registration', 'error')
                print(f"Database error: {e}")
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection error', 'error')
    
    # For GET requests or if registration fails
    return render_template('register.html')


from decimal import Decimal, getcontext

@app.route('/booking-confirmation', methods=['GET', 'POST'])
def booking_confirmation():
    if 'loggedin' not in session:
        flash('Please login to confirm booking', 'danger')
        return redirect(url_for('login'))

    if request.method == 'GET':
        # Existing GET handling code remains the same
        room_type_id = request.args.get('room_type_id')
        check_in = request.args.get('check_in')
        check_out = request.args.get('check_out')

        if not all([room_type_id, check_in, check_out]):
            flash('Missing booking details', 'danger')
            return redirect(url_for('search_form'))

        try:
            room_type_id = int(room_type_id)
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
            nights = (check_out_date - check_in_date).days
            if nights <= 0:
                flash("Check-out must be after check-in", "danger")
                return redirect(url_for('search_form'))
        except Exception as e:
            print(f"Date parsing error: {e}")
            flash("Invalid date format", "danger")
            return redirect(url_for('search_form'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Prevent overlapping booking
            cursor.execute("""
                SELECT 1 FROM bookings 
                WHERE user_id = %s
                AND (
                    (check_in_date BETWEEN %s AND %s)
                    OR (check_out_date BETWEEN %s AND %s)
                    OR (%s BETWEEN check_in_date AND check_out_date)
                    OR (%s BETWEEN check_in_date AND check_out_date)
                )
            """, (
                session['user_id'],
                check_in_date, check_out_date,
                check_in_date, check_out_date,
                check_in_date, check_out_date
            ))
            if cursor.fetchone():
                flash("You already have a booking during these dates!", "danger")
                return redirect(url_for('dashboard'))

            # Get room and hotel info
            cursor.execute("""
                SELECT rt.*, h.hotel_id, h.name AS hotel_name, h.city, h.country
                FROM room_types rt
                JOIN hotels h ON rt.hotel_id = h.hotel_id
                WHERE rt.room_type_id = %s
            """, (room_type_id,))
            result = cursor.fetchone()

            if not result:
                flash("Room type not found", "danger")
                return redirect(url_for('search_form'))
            
            def format_currency(value):
                return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"
            
            base_price = Decimal(str(result['base_price']))
            nights = int(nights)
            subtotal = base_price * nights
            tax = subtotal * Decimal('0.18')
            total_amount = subtotal + tax

            # Format currency for display
            subtotal_display = format_currency(subtotal)
            tax_display = format_currency(tax)
            total_display = format_currency(total_amount)

            # Split into two dicts for template compatibility
            hotel = {
                'hotel_id': result['hotel_id'],
                'name': result['hotel_name'],
                'city': result['city'],
                'country': result['country']
            }

            room_type = {
                'room_type_id': result['room_type_id'],
                'name': result['name'],
                'base_price': base_price
            }

            return render_template('booking_confirmation.html',
                                hotel=hotel,
                                room_type=room_type,
                                check_in=check_in_date,
                                check_out=check_out_date,
                                nights=nights,
                                subtotal_display=subtotal_display,
                                tax_display=tax_display,
                                total_display=total_display,
                                total_amount=total_amount)

        except Exception as e:
            print(f"Error in booking confirmation: {e}")
            flash("An error occurred", "danger")
            return redirect(url_for('search_form'))
        finally:
            cursor.close()
            conn.close()

    elif request.method == 'POST':
    # Handle the booking confirmation POST
        room_type_id = request.form.get('room_type_id')
        hotel_id = request.form.get('hotel_id')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        total_amount = request.form.get('total_amount')

    try:
        room_type_id = int(room_type_id)
        hotel_id = int(hotel_id)
        total_amount = Decimal(total_amount)
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        nights = (check_out_date - check_in_date).days
    except Exception as e:
        print(f"Error parsing form data: {e}")
        flash("Invalid booking data", "danger")
        return redirect(url_for('search_form'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get room type price
        cursor.execute("SELECT base_price FROM room_types WHERE room_type_id = %s", (room_type_id,))
        room_price = cursor.fetchone()[0]

        # Create the booking
        cursor.execute("""
            INSERT INTO bookings (
                user_id, hotel_id,
                check_in_date, check_out_date, total_amount,
                booking_date, status
            ) VALUES (
                %s, %s,
                %s, %s, %s,
                NOW(), 'confirmed'
            )
        """, (
            session['user_id'], hotel_id,
            check_in_date, check_out_date, total_amount
        ))
        booking_id = cursor.lastrowid

        # Add booking room details (without room_id since it's not in your schema)
        cursor.execute("""
            INSERT INTO booking_rooms (
                booking_id, room_type_id,
                quantity, adults, children, price_per_night
            ) VALUES (
                %s, %s,
                1, 1, 0, %s
            )
        """, (booking_id, room_type_id, room_price))

        conn.commit()

        return redirect(url_for('booking_success'))

    except Exception as e:
        conn.rollback()
        print(f"Error creating booking: {e}")
        flash("An error occurred while processing your booking", "danger")
        return redirect(url_for('search_form'))
    finally:
        cursor.close()
        conn.close()
@app.route('/booking-success')
def booking_success():
    if 'loggedin' not in session:
        flash('Please login to view booking history', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = datetime.now().date()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get active bookings (check_out_date >= today)
        cursor.execute("""
            SELECT b.*, h.name as hotel_name, h.city, h.country, rt.name as room_type_name,
                   br.quantity, br.adults, br.children, br.price_per_night,
                   DATEDIFF(b.check_out_date, b.check_in_date) as nights
            FROM bookings b
            JOIN hotels h ON b.hotel_id = h.hotel_id
            JOIN booking_rooms br ON b.booking_id = br.booking_id
            JOIN room_types rt ON br.room_type_id = rt.room_type_id
            WHERE b.user_id = %s AND b.check_out_date >= %s
            ORDER BY b.check_in_date ASC
        """, (user_id, today))
        active_bookings = cursor.fetchall()

        # Get past bookings (check_out_date < today)
        cursor.execute("""
            SELECT b.*, h.name as hotel_name, h.city, h.country, rt.name as room_type_name,
                   br.quantity, br.adults, br.children, br.price_per_night,
                   DATEDIFF(b.check_out_date, b.check_in_date) as nights
            FROM bookings b
            JOIN hotels h ON b.hotel_id = h.hotel_id
            JOIN booking_rooms br ON b.booking_id = br.booking_id
            JOIN room_types rt ON br.room_type_id = rt.room_type_id
            WHERE b.user_id = %s AND b.check_out_date < %s
            ORDER BY b.check_in_date DESC
        """, (user_id, today))
        past_bookings = cursor.fetchall()

        return render_template('booking_success.html',
                            active_bookings=active_bookings,
                            past_bookings=past_bookings,
                            today=today)

    except Exception as e:
        print(f"Error in booking_success: {e}")
        flash("An error occurred while retrieving your bookings", "danger")
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()
@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'loggedin' not in session:
        flash('Please login to cancel bookings', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Use dictionary cursor for easier access
    
    try:
        # First verify the booking exists and belongs to the user
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE booking_id = %s AND user_id = %s
        """, (booking_id, user_id))
        booking = cursor.fetchone()
        
        if not booking:
            flash("Booking not found or you don't have permission to cancel it", "danger")
            return redirect(url_for('dashboard'))
        
        # Check if booking is already cancelled
        if booking['status'] == 'cancelled':
            flash("This booking is already cancelled", "warning")
            return redirect(url_for('dashboard'))
            
        # Update the booking status
        cursor.execute("""
            UPDATE bookings 
            SET status = 'cancelled'
            WHERE booking_id = %s
        """, (booking_id,))
        
        conn.commit()
        flash("Booking cancelled successfully", "success")
        
    except Exception as e:
        conn.rollback()
        print(f"Error cancelling booking: {str(e)}")
        flash("An error occurred while cancelling the booking", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))


# Admin credentials (in production, store these in a database or environment variables)
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': generate_password_hash('admin123')  # Hashed password
}

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and check_password_hash(ADMIN_CREDENTIALS['password'], password):
            session['admin_logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/admin/hotels')
def manage_hotels():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get hotels with their primary images
        cursor.execute("""
            SELECT h.*, hi.image_url as primary_image
            FROM hotels h
            LEFT JOIN hotel_images hi ON h.hotel_id = hi.hotel_id AND hi.is_primary = TRUE
            ORDER BY h.name
        """)
        hotels = cursor.fetchall()
        
        return render_template('manage_hotels.html', 
                            hotels=hotels,
                            title="Manage Hotels")
    
    except Exception as e:
        print(f"Error fetching hotels: {str(e)}")
        flash("Error loading hotels", "danger")
        return redirect(url_for('admin_dashboard'))
    
    finally:
        cursor.close()
        conn.close()
@app.route('/admin/hotels/add', methods=['GET', 'POST'])
def add_hotel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        conn = None
        cursor = None
        try:
            # Get form data
            name = request.form['name']
            description = request.form['description']
            address = request.form['address']
            city = request.form['city']
            country = request.form['country']
            star_rating = float(request.form['star_rating'])
            contact_phone = request.form['contact_phone']
            contact_email = request.form['contact_email']
            is_active = 'is_active' in request.form

            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert hotel
            cursor.execute("""
                INSERT INTO hotels 
                (name, description, address, city, country, star_rating, contact_phone, contact_email, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, description, address, city, country, star_rating, contact_phone, contact_email, is_active))

            hotel_id = cursor.lastrowid

            # Handle image upload - simplified version
            if 'primary_image' in request.files:
                image = request.files['primary_image']
                if image.filename != '':
                    # Just save with original filename (be aware of security implications)
                    filename = image.filename
                    image.save(f"static/uploads/{filename}")
                    
                    cursor.execute("""
                        INSERT INTO hotel_images 
                        (hotel_id, image_url, is_primary)
                        VALUES (%s, %s, TRUE)
                    """, (hotel_id, f'/static/uploads/{filename}'))

            conn.commit()
            flash('Hotel added successfully!', 'success')
            return redirect(url_for('manage_hotels'))

        except Exception as e:
            if conn:
                conn.rollback()
            flash(f'Error adding hotel: {str(e)}', 'danger')
            return redirect(url_for('add_hotel'))

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('add_hotel.html', title="Add Hotel")

@app.route('/admin/hotels/edit/<int:hotel_id>', methods=['GET', 'POST'])
def edit_hotel(hotel_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            # Get form data
            name = request.form['name']
            description = request.form['description']
            address = request.form['address']
            city = request.form['city']
            country = request.form['country']
            star_rating = float(request.form['star_rating'])
            contact_phone = request.form['contact_phone']
            contact_email = request.form['contact_email']
            is_active = 'is_active' in request.form

            # Update hotel
            cursor.execute("""
                UPDATE hotels SET
                    name = %s, description = %s, address = %s,
                    city = %s, country = %s, star_rating = %s,
                    contact_phone = %s, contact_email = %s, is_active = %s
                WHERE hotel_id = %s
            """, (name, description, address, city, country, star_rating, 
                 contact_phone, contact_email, is_active, hotel_id))

            # Handle image upload
            if 'primary_image' in request.files:
                image = request.files['primary_image']
                if image.filename != '':
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'hotels', filename)
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    image.save(image_path)

                    # Update or insert image
                    cursor.execute("""
                        INSERT INTO hotel_images 
                        (hotel_id, image_url, is_primary)
                        VALUES (%s, %s, TRUE)
                        ON DUPLICATE KEY UPDATE image_url = VALUES(image_url)
                    """, (hotel_id, f'/static/uploads/hotels/{filename}'))

            conn.commit()
            flash('Hotel updated successfully!', 'success')
            return redirect(url_for('manage_hotels'))

        # GET request - fetch hotel data
        cursor.execute("SELECT * FROM hotels WHERE hotel_id = %s", (hotel_id,))
        hotel = cursor.fetchone()

        if not hotel:
            flash('Hotel not found', 'danger')
            return redirect(url_for('manage_hotels'))

        # Get primary image if exists
        cursor.execute("SELECT image_url FROM hotel_images WHERE hotel_id = %s AND is_primary = TRUE", (hotel_id,))
        image = cursor.fetchone()
        hotel['primary_image'] = image['image_url'] if image else None

        return render_template('edit_hotel.html', hotel=hotel,
                            title="Edit Hotel")

    except Exception as e:
        conn.rollback()
        flash(f'Error updating hotel: {str(e)}', 'danger')
        return redirect(url_for('edit_hotel', hotel_id=hotel_id))

    finally:
        cursor.close()
        conn.close()
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/rooms')
def manage_rooms():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT r.room_id, r.room_number, r.floor_number, r.is_active,
                   rt.name AS room_type, rt.base_price, rt.max_occupancy,
                   h.name AS hotel_name, h.hotel_id
            FROM rooms r
            JOIN room_types rt ON r.room_type_id = rt.room_type_id
            JOIN hotels h ON r.hotel_id = h.hotel_id
            ORDER BY h.name, r.room_number
        """)
        rooms = cursor.fetchall()
        
        return render_template('manage_rooms.html', 
                            rooms=rooms,
                            title="Manage Rooms")
    
    except Exception as e:
        print(f"Error fetching rooms: {str(e)}")
        flash("Error loading rooms", "danger")
        return redirect(url_for('admin_dashboard'))
    
    finally:
        cursor.close()
        conn.close()
@app.route('/admin/rooms/add', methods=['GET', 'POST'])
def add_room():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            # Get form data
            room_type_id = int(request.form['room_type_id'])
            hotel_id = int(request.form['hotel_id'])
            room_number = request.form['room_number']
            floor_number = request.form.get('floor_number')
            is_active = 'is_active' in request.form

            # Insert room
            cursor.execute("""
                INSERT INTO rooms 
                (room_type_id, hotel_id, room_number, floor_number, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """, (room_type_id, hotel_id, room_number, floor_number, is_active))

            conn.commit()
            flash('Room added successfully!', 'success')
            return redirect(url_for('manage_rooms'))

        # GET request - fetch data for dropdowns
        cursor.execute("SELECT hotel_id, name FROM hotels WHERE is_active = TRUE ORDER BY name")
        hotels = cursor.fetchall()

        cursor.execute("SELECT room_type_id, name FROM room_types ORDER BY name")
        room_types = cursor.fetchall()

        return render_template('add_room.html',
                       hotels=hotels,
                       room_types=room_types,
                       title="Add Room")


    except Exception as e:
        conn.rollback()
        flash(f'Error adding room: {str(e)}', 'danger')
        return redirect(url_for('add_room'))

    finally:
        cursor.close()
        conn.close()
@app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'POST':
            # Get form data
            room_type_id = int(request.form['room_type_id'])
            hotel_id = int(request.form['hotel_id'])
            room_number = request.form['room_number']
            floor_number = request.form.get('floor_number')
            is_active = 'is_active' in request.form

            # Update room
            cursor.execute("""
                UPDATE rooms SET
                    room_type_id = %s, hotel_id = %s,
                    room_number = %s, floor_number = %s,
                    is_active = %s
                WHERE room_id = %s
            """, (room_type_id, hotel_id, room_number, floor_number, is_active, room_id))

            conn.commit()
            flash('Room updated successfully!', 'success')
            return redirect(url_for('manage_rooms'))

        # GET request - fetch room data
        cursor.execute("""
            SELECT r.*, rt.name AS room_type_name, h.name AS hotel_name
            FROM rooms r
            JOIN room_types rt ON r.room_type_id = rt.room_type_id
            JOIN hotels h ON r.hotel_id = h.hotel_id
            WHERE r.room_id = %s
        """, (room_id,))
        room = cursor.fetchone()

        if not room:
            flash('Room not found', 'danger')
            return redirect(url_for('manage_rooms'))

        # Fetch data for dropdowns
        cursor.execute("SELECT hotel_id, name FROM hotels WHERE is_active = TRUE ORDER BY name")
        hotels = cursor.fetchall()

        cursor.execute("SELECT room_type_id, name FROM room_types ORDER BY name")
        room_types = cursor.fetchall()

        return render_template('edit_room.html',
                       room=room,
                       hotels=hotels,
                       room_types=room_types,
                       title="Edit Room")


    except Exception as e:
        conn.rollback()
        flash(f'Error updating room: {str(e)}', 'danger')
        return redirect(url_for('edit_room', room_id=room_id))

    finally:
        cursor.close()
        conn.close()
@app.route('/admin/rooms/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
        conn.commit()
        flash('Room deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error deleting room. Make sure there are no related bookings.', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('manage_rooms'))
@app.route('/admin/hotels/delete/<int:hotel_id>', methods=['POST'])
def delete_hotel(hotel_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First delete dependent records (hotel_images)
        cursor.execute("DELETE FROM hotel_images WHERE hotel_id = %s", (hotel_id,))
        
        # Then delete the hotel
        cursor.execute("DELETE FROM hotels WHERE hotel_id = %s", (hotel_id,))
        
        conn.commit()
        flash('Hotel deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        print(f"Error deleting hotel: {str(e)}")
        flash('Error deleting hotel. Please try again.', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('manage_hotels'))

if __name__ == '__main__':
    app.run(debug=True)