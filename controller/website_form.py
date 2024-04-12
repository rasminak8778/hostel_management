from odoo import http, _
from odoo.http import request


class WebsiteForm(http.Controller):
    @http.route(['/student'], type='http', auth="public", website=True)
    def room(self):
        """function defined to search available rooms that will show in webpage
        """
        rooms = (request.env['room.management'].sudo().search
                 ([('state', 'in', ('empty', 'partial'))]))
        values = {}
        values.update({
            'rooms': rooms
        })
        return (request.render
                ("hostel_management.online_student_registration_form", values))

    @http.route(['/create/student/'], type='http', auth="public",
                website=True)
    def create_student(self, **kw):
        """function for creating a student record in hostel management module
        through website"""
        print('kw', kw)
        if kw.get('email'):
            email = kw.get('email')
            existing_record = (request.env['student.information'].sudo()
                               .search([('email', '=', email)]))
            if existing_record:
                values = {'error': _("This Email Id Already Exist")}
                return request.render(
                    "hostel_management.online_student_registration_form",
                    values)
            else:
                request.env['student.information'].sudo().create(kw)
                return request.render(
                    "hostel_management.online_student_thankyou_form", {})
        else:
            return request.redirect('/student')
