from odoo import http
from odoo.http import request


class RoomForms(http.Controller):
    @http.route(['/latest-rooms'], type='json', auth="public")
    def latest_room(self):
        """function for searching the latest 4 rooms and redirect to room view
        in dynamic snippet
        """
        latest_room = (request.env['room.management'].sudo().
                       search_read([], order='create_date desc'))
        room_list = [latest_room[i:i+4] for i in range(0, len(latest_room), 4)]
        print('rrr', len(room_list[0]))
        return room_list
