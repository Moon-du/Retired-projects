class Region:
    """设置区域信息"""

    def __init__(self, city):
        """初始化区域属性"""
        self.city = city
        self.latitude = "30.52729618448312"
        self.longitude = "104.0850490905795"
        self.region_info = {
            "济南": "3701",
            "青岛": "3702",
            "淄博": "3703",
            "枣庄": "3704",
            "东营": "3705",
            "烟台": "3706",
            "潍坊": "3707",
            "济宁": "3708",
            "泰安": "3709",
            "威海": "3710",
            "日照": "3711",
            "临沂": "3713",
            "德州": "3714",
            "聊城": "3715",
            "滨州": "3716",
            "菏泽": "3717",
            "广州": "4401",
            "重庆": "5001",
            "成都": "5101",
            "天津": "1201",
            "郑州": "4101",
        }

    def get_region_info(self):
        """获取区域信息"""
        return {
            'region_code': self.region_info[self.city],
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


if __name__ == '__main__':
    Region("济南").get_region_info()
