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
        partner = order.partner_shipping_id or order.partner_id
        # nếu partner chưa geocode
        if not (partner.latitude and partner.longitude):
            order.message_post(body=_("Khách hàng chưa có tọa độ lat/lon"))
            return []

        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', order.company_id.id)
        ])
        assigned = []
        for line in order.order_line.filtered(lambda l: l.product_id.type=='product'):
            nearest_wh, min_dist = False, float('inf')
            for wh in warehouses:
                # kiểm tra tồn kho bình thường...
                # tính khoảng cách
                dist = wh.calculate_distance_to_partner(partner)
                if dist < min_dist:
                    min_dist, nearest_wh = dist, wh
            if nearest_wh and min_dist < float('inf'):
                line.warehouse_id = nearest_wh.id
                assigned.append(nearest_wh)
        return assigned

    def _find_nearest_warehouse_with_stock(self):
        self.ensure_one()
        partner = self.partner_shipping_id or self.partner_id
        if not (partner.latitude and partner.longitude):
            return None, False

        # tìm các kho có đủ hàng
        warehouses = self.env['stock.warehouse'].search([
            ('company_id','=',self.company_id.id)
        ])
        candidate = warehouses.filtered(lambda wh: all(
            sum(q.quantity-q.reserved_quantity for q in self.env['stock.quant'].search([
                ('product_id','=',l.product_id.id),
                ('location_id','=', wh.lot_stock_id.id),
            ])) >= l.product_uom_qty
            for l in self.order_line.filtered(lambda l: l.product_id.type=='product')
        ))
        # tính khoảng cách và loại bỏ +∞
        wh_dist = [(wh, wh.calculate_distance_to_partner(partner)) for wh in candidate]
        wh_dist = [t for t in wh_dist if t[1] < float('inf')]
        if not wh_dist:
            return None, False
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