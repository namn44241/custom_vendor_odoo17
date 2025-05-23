from odoo import api, fields, models

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    # Không cần tọa độ riêng nữa, sử dụng state
    
    def calculate_distance_to_partner(self, partner):
        """Tính khoảng cách từ kho đến đối tác dựa trên state"""
        if not partner or not partner.state_id or not partner.state_id.code:
            return 9999
            
        company_partner = self.company_id.partner_id
        
        # Nếu cùng state thì khoảng cách = 0
        if company_partner.state_id and company_partner.state_id == partner.state_id:
            return 0
            
        # Nếu khác state thì dùng bảng tọa độ
        if not company_partner.state_id or not company_partner.state_id.code:
            return 9999
            
        return self.env['res.country.state.position'].calculate_distance(
            company_partner.state_id.code, 
            partner.state_id.code
        )

    def get_location_score(self, partner):
        """Tính điểm ưu tiên kho dựa trên vị trí địa lý
        - Cùng city: 100 điểm
        - Cùng country: 50 điểm
        - Khác cả hai: 0 điểm
        """
        score = 0
        
        # Lấy thông tin city và country của kho
        company_partner = self.company_id.partner_id
        
        # So sánh City
        if company_partner.city and partner.city and company_partner.city.lower() == partner.city.lower():
            score += 100
        
        # So sánh Country
        if company_partner.country_id and partner.country_id and company_partner.country_id == partner.country_id:
            score += 50
        
        return score 