from odoo import http
from odoo.http import request


class RoomDetails(http.Controller):
    @http.route(['/rooms/<int:rec_id>/'], type='http',
                auth="public", website=True)
    def room_details(self, rec_id):
        data = request.env['room.management'].sudo().browse(rec_id)
        value = {
            'data': data,
        }
        return request.render('hostel_management.online_room_details_form',
                              value)
