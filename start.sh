#!/bin/bash

# Script to start the Django development server

echo "Starting Django Education System..."
echo "===================================="
echo ""
echo "Admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Manager credentials:"
echo "  Username: manager"
echo "  Password: manager123"
echo ""
echo "Employee credentials:"
echo "  Username: employee"
echo "  Password: employee123"
echo ""
echo "===================================="
echo ""

python3 manage.py runserver 0.0.0.0:8000
