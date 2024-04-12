/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToElement } from "@web/core/utils/render";


    publicWidget.registry.room_snippet = publicWidget.Widget.extend({
        selector: '.dynamic_snippet_blog',
        start: function(){
            var self = this
            jsonrpc('/latest-rooms').then(function(data){
                data[0].is_active = true
                data[0].number = Math.floor(Math.random() * 90000) + 10000;
                self.$el.find('#carousel').html(renderToElement("hostel_management.latest_room_snippet_carousel",{data:data}))
            })
        },
    });

