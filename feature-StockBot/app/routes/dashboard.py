from flask import Blueprint, render_template, redirect, url_for

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard_root():
    return render_template('dashboard/index.html')

@dashboard_bp.route('/dashboard')
def dashboard_index():
    return render_template('dashboard/index.html') 