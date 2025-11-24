#!/usr/bin/env python3
"""
VC Portfolio Management System - Application Entry Point
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("VC Portfolio Management System")
    print("=" * 60)
    print("\nStarting server...")
    print("Access the application at: http://localhost:5000")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60)
    print()

    app.run(debug=True, host='0.0.0.0', port=5000)
