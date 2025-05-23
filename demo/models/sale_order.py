from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def action_confirm(self):
        for order in self:
            self._assign_nearest_warehouse(order)
        return super(SaleOrder, self).action_confirm()
    
    def action_assign_nearest_warehouse(self):
        """Phương thức public để gọi từ button"""
        for order in self:
            assigned_warehouses = self._assign_nearest_warehouse(order)
            if assigned_warehouses:
                warehouse_names = ', '.join([w.name for w in assigned_warehouses])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Thành công'),
                        'message': _("Đã chọn kho gần nhất cho đơn hàng: %s") % warehouse_names,
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Cảnh báo'),
                        'message': _("Không tìm thấy kho phù hợp hoặc khách hàng không có tọa độ GPS."),
                        'sticky': False,
                        'type': 'warning',
                    }
                }
    
    def _assign_nearest_warehouse(self, order):
        """Gán kho gần nhất có đủ hàng cho mỗi dòng."""
        partner = order.partner_shipping_id or order.partner_id
        if not partner.state_id or not partner.state_id.code:
            order.message_post(body=_("Khách hàng không có Province/State để tính khoảng cách"))
            return []

        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', order.company_id.id)
        ])
        if not warehouses:
            order.message_post(body=_("Không tìm thấy warehouse trong công ty"))
            return []

        assigned = []
        for line in order.order_line.filtered(lambda l: l.product_id.type=='product'):
            nearest_wh, min_dist = False, float('inf')
            for wh in warehouses:
                # kiểm tra tồn kho
                quant_ids = self.env['stock.quant'].search([
                    ('product_id','=', line.product_id.id),
                    ('location_id','=', wh.lot_stock_id.id),
                ])
                avail = sum(q.quantity - q.reserved_quantity for q in quant_ids)
                if avail < line.product_uom_qty:
                    continue
                # tính khoảng cách đúng
                dist = wh.calculate_distance_to_partner(partner)
                if dist < min_dist:
                    min_dist, nearest_wh = dist, wh
            if nearest_wh:
                line.warehouse_id = nearest_wh.id
                assigned.append(nearest_wh)
        return assigned

    def _find_nearest_warehouse_with_stock(self):
        """Tìm 1 warehouse gần nhất có đủ hàng cho toàn bộ đơn."""
        self.ensure_one()
        partner = self.partner_shipping_id or self.partner_id
        if not partner.state_id or not partner.state_id.code:
            return None, False

        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id)
        ])
        # lọc những kho có đủ hàng cho tất cả order_line
        candidate = warehouses.filtered(lambda wh: all(
            sum(q.quantity-q.reserved_quantity for q in self.env['stock.quant'].search([
                ('product_id','=', l.product_id.id),
                ('location_id','=', wh.lot_stock_id.id),
            ])) >= l.product_uom_qty
            for l in self.order_line.filtered(lambda l: l.product_id.type=='product')
        ))
        if not candidate:
            return None, False

        # tính khoảng cách và chọn kho nhỏ nhất
        wh_dist = [(wh, wh.calculate_distance_to_partner(partner)) for wh in candidate]
        wh_dist.sort(key=lambda x: x[1])
        return wh_dist[0][0], True

    def action_open_warehouse_finder(self):
        """Mở wizard tìm kho"""
        self.ensure_one()
        
        return {
            'name': _('Tìm kho gần nhất'),
            'type': 'ir.actions.act_window',
            'res_model': 'warehouse.finder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        } 