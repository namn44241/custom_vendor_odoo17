from odoo import api, fields, models
import math

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
        
    def calculate_distance_to_partner(self, partner):
        """Tính khoảng cách Haversine hoàn toàn dựa trên lat/long.
        Nếu kho hoặc khách hàng chưa có lat/lon, trả về +∞ để bỏ qua."""
        self.ensure_one()
        wh_partner = self.partner_id or self.company_id.partner_id

        lat1, lon1 = wh_partner.latitude, wh_partner.longitude
        lat2, lon2 = partner.latitude, partner.longitude
        if not all([lat1, lon1, lat2, lon2]):
            return float('inf')

        R = 6371.0  
        φ1, φ2 = math.radians(lat1), math.radians(lat2)
        Δφ = math.radians(lat2 - lat1)
        Δλ = math.radians(lon2 - lon1)
        a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def get_location_score(self, partner):
        """Tính điểm ưu tiên kho dựa trên vị trí địa lý
        - Cùng city: 100 điểm
        - Cùng country: 50 điểm
        - Khác cả hai: 0 điểm
        """
        score = 0
        company_partner = self.company_id.partner_id
        if company_partner.city and partner.city and company_partner.city.lower() == partner.city.lower():
            score += 100
        if company_partner.country_id and partner.country_id and company_partner.country_id == partner.country_id:
            score += 50
        
        return score 