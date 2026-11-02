from app import app, db, User

with app.app_context():
    admin = User.query.filter_by(
        username="koushik reddy"
    ).first()

    admin.email = "basika.koushik123@gmail.com"
    admin.role = "admin"
    admin.set_password("Admin@12345")

    db.session.commit()

    print("Admin updated successfully!")
    print("Role:", admin.role)
    print("Password check:", admin.check_password("Admin@12345"))