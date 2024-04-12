from odoo import http
from odoo.http import request


class RoomForm(http.Controller):
    @http.route(['/room'], type='http', auth="public", website=True)
    def room(self):
        """function for searching the latest 4 rooms and redirect to room view
        """
        latest_rooms = (request.env['room.management'].sudo().
                        search([], order='create_date desc', limit=4))
        print('a', latest_rooms)
        values = {}
        values.update({
            'latest_rooms': latest_rooms,
        })
        return (request.render
                ("hostel_management.online_room_view_form", values))


