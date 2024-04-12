from odoo import http
from odoo.http import request


class RoomDetailsForm(http.Controller):
    @http.route(['/room/details/<int:rec_id>/'], type='http',
                auth="public", website=True)
    def room(self, rec_id):
        """function for retrieving the room object with id and show
        the details in webpage"""
        data = request.env['room.management'].sudo().browse(rec_id)
        values = {
            'data': data

        }
        return request.render("hostel_management.online_room_details_form",
                              values)
