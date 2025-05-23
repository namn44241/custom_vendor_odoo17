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
        """Gán kho gần nhất có hàng cho từng dòng đơn hàng"""
        # Lấy vị trí khách hàng
        partner = order.partner_shipping_id or order.partner_id
        
        # Debug log
        _logger.info(f"Đang xử lý đơn hàng: {order.name}")
        _logger.info(f"Khách hàng: {partner.name}")
        _logger.info(f"Tọa độ: {partner.latitude}, {partner.longitude}")
        
        if not partner.latitude or not partner.longitude:
            _logger.warning("Khách hàng không có tọa độ GPS!")
            return False
        
        # Tìm tất cả kho của công ty
        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', order.company_id.id)
        ])
        
        _logger.info(f"Số lượng kho tìm thấy: {len(warehouses)}")
        for w in warehouses:
            _logger.info(f"Kho: {w.name}, Tọa độ: {w.latitude}, {w.longitude}")
        
        if not warehouses:
            _logger.warning("Không tìm thấy kho nào!")
            return False
        
        assigned_warehouses = set()
        
        for line in order.order_line:
            # Kiểm tra xem sản phẩm có cần quản lý kho không
            _logger.info(f"Loại sản phẩm: {line.product_id.type}")
            if line.product_id.type != 'product':
                _logger.warning(f"Sản phẩm {line.product_id.name} không phải loại 'product'")
                continue
            
            _logger.info(f"Xử lý dòng đơn hàng: {line.product_id.name}, Số lượng: {line.product_uom_qty}")
            
            # Tìm kho gần nhất có đủ hàng
            nearest_warehouse = False
            min_distance = float('inf')
            
            for warehouse in warehouses:
                _logger.info(f"Kiểm tra kho: {warehouse.name}")
                _logger.info(f"Tọa độ kho: {warehouse.latitude}, {warehouse.longitude}")
                
                # Kiểm tra tồn kho
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id.warehouse_id', '=', warehouse.id),
                    ('location_id.usage', '=', 'internal'),
                ])
                
                available_qty = sum(q.quantity - q.reserved_quantity for q in quants)
                _logger.info(f"Lượng tồn kho: {available_qty}")
                
                if available_qty < line.product_uom_qty:
                    _logger.info("Kho không đủ hàng!")
                    continue
                
                # Tính khoảng cách
                distance = warehouse.calculate_distance(
                    partner.latitude,
                    partner.longitude
                )
                _logger.info(f"Khoảng cách: {distance} km")
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_warehouse = warehouse
            
            if nearest_warehouse:
                _logger.info(f"Đã chọn kho: {nearest_warehouse.name}")
                assigned_warehouses.add(nearest_warehouse)
                line.warehouse_id = nearest_warehouse.id
                line.name = f"{line.name}\n(Kho được chọn: {nearest_warehouse.name})"
        
        return list(assigned_warehouses)

    def _find_nearest_warehouse_with_stock(self):
        """Tìm kho gần nhất có đủ hàng dựa trên tỉnh thành"""
        self.ensure_one()
        
        # Sử dụng địa chỉ giao hàng hoặc địa chỉ đối tác
        partner = self.partner_shipping_id or self.partner_id
        if not partner:
            return None, False
        
        # Lấy tất cả kho thuộc công ty hiện tại
        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id)
        ])
        
        if not warehouses:
            return None, False
        
        # Kiểm tra từng kho có đủ hàng không
        available_warehouses = []
        
        for warehouse in warehouses:
            all_available = True
            
            for line in self.order_line:
                if line.product_id.type != 'product':
                    continue
                    
                # Kiểm tra tồn kho
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', warehouse.lot_stock_id.id)
                ])
                
                available_qty = sum(q.quantity - q.reserved_quantity for q in quants)
                if available_qty < line.product_uom_qty:
                    all_available = False
                    break
            
            if all_available:
                available_warehouses.append(warehouse)
        
        if not available_warehouses:
            return None, False
        
        # Tìm kho gần nhất trong số kho có đủ hàng
        warehouse_distances = [(wh, wh.calculate_distance_to_partner(partner)) for wh in available_warehouses]
        nearest_warehouse = min(warehouse_distances, key=lambda x: x[1])[0]
        
        return nearest_warehouse, True

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