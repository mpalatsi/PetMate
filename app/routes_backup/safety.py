from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models import db, EmergencyContact, User
from app.utils.decorators import login_required

bp = Blueprint('safety', __name__)

@bp.route('/emergency-contacts')
@login_required
def emergency_contacts():
    user = User.query.filter_by(username=session['username']).first()
    contacts = EmergencyContact.query.filter_by(user_id=user.id).all()
    return render_template('emergency_contacts.html', emergency_contacts=contacts)

@bp.route('/emergency-contacts/add', methods=['POST'])
@login_required
def add_emergency_contact():
    user = User.query.filter_by(username=session['username']).first()
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    relationship = request.form.get('relationship')
    is_primary = bool(request.form.get('is_primary'))
    
    if not all([name, phone, relationship]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('safety.emergency_contacts'))
    
    # If this is marked as primary, unmark other primary contacts
    if is_primary:
        EmergencyContact.query.filter_by(user_id=user.id, is_primary=True).update({'is_primary': False})
    
    contact = EmergencyContact(
        user_id=user.id,
        name=name,
        phone=phone,
        relationship=relationship,
        is_primary=is_primary
    )
    
    db.session.add(contact)
    db.session.commit()
    
    flash('Emergency contact added successfully.', 'success')
    return redirect(url_for('safety.emergency_contacts'))

@bp.route('/emergency-contacts/<int:contact_id>/edit', methods=['POST'])
@login_required
def edit_emergency_contact(contact_id):
    user = User.query.filter_by(username=session['username']).first()
    contact = EmergencyContact.query.get_or_404(contact_id)
    
    # Verify ownership
    if contact.user_id != user.id:
        flash('You do not have permission to edit this contact.', 'error')
        return redirect(url_for('safety.emergency_contacts'))
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    relationship = request.form.get('relationship')
    is_primary = bool(request.form.get('is_primary'))
    
    if not all([name, phone, relationship]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('safety.emergency_contacts'))
    
    # If this is marked as primary, unmark other primary contacts
    if is_primary and not contact.is_primary:
        EmergencyContact.query.filter_by(user_id=user.id, is_primary=True).update({'is_primary': False})
    
    contact.name = name
    contact.phone = phone
    contact.relationship = relationship
    contact.is_primary = is_primary
    
    db.session.commit()
    
    flash('Emergency contact updated successfully.', 'success')
    return redirect(url_for('safety.emergency_contacts'))

@bp.route('/emergency-contacts/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_emergency_contact(contact_id):
    user = User.query.filter_by(username=session['username']).first()
    contact = EmergencyContact.query.get_or_404(contact_id)
    
    # Verify ownership
    if contact.user_id != user.id:
        return jsonify({'error': 'You do not have permission to delete this contact.'}), 403
    
    # Check if this is the only primary contact
    if contact.is_primary and not EmergencyContact.query.filter_by(
        user_id=user.id, is_primary=True).filter(EmergencyContact.id != contact_id).first():
        return jsonify({'error': 'Cannot delete the only primary emergency contact.'}), 400
    
    db.session.delete(contact)
    db.session.commit()
    
    return jsonify({'message': 'Contact deleted successfully.'})

@bp.route('/api/emergency-contacts/<int:contact_id>')
@login_required
def get_emergency_contact(contact_id):
    user = User.query.filter_by(username=session['username']).first()
    contact = EmergencyContact.query.get_or_404(contact_id)
    
    # Verify ownership
    if contact.user_id != user.id:
        return jsonify({'error': 'You do not have permission to view this contact.'}), 403
    
    return jsonify({
        'id': contact.id,
        'name': contact.name,
        'phone': contact.phone,
        'relationship': contact.relationship,
        'is_primary': contact.is_primary
    }) 