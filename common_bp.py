from flask import Blueprint, render_template

common_bp = Blueprint('common', __name__)

@common_bp.route('/header')
def header():
    return render_template('header.html')

@common_bp.route('/footer')
def footer():
    return render_template('footer.html')