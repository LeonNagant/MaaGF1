"""
配置管理模块
负责加载和管理应用程序配置
"""
import os

class Config:
    """配置管理类"""
    
    def __init__(self):
        self.bot_token = None
        self.chat_id = None
        self.webhook_key = None
        self.default_ext_notify = None
        self.telegram_loaded = False
        self.wechat_loaded = False
    
    def load_config(self, config_path=None):
        """
        加载配置文件
        """
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "agent.conf")
        
        print(f"尝试加载配置文件: {config_path}")
        
        if not os.path.exists(config_path):
            print(f"配置文件不存在: {config_path}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'Bot_Token':
                            self.bot_token = value
                            print(f"已加载 Bot_Token: {self.bot_token[:10] if self.bot_token else 'None'}...")
                        elif key == 'Chat_ID':
                            self.chat_id = value
                            print(f"已加载 Chat_ID: {self.chat_id}")
                        elif key == 'Webhook_Key':
                            self.webhook_key = value
                            print(f"已加载 Webhook_Key: {self.webhook_key[:10] if self.webhook_key else 'None'}...")
                        elif key == 'Default_ExtNotify':
                            self.default_ext_notify = value.lower()
                            print(f"已加载 Default_ExtNotify: {self.default_ext_notify}")
            
            # 检查Telegram配置
            if self.bot_token and self.chat_id:
                print("Telegram配置加载成功")
                self.telegram_loaded = True
            else:
                print("Telegram配置不完整")
                self.telegram_loaded = False
            
            # 检查企业微信配置
            if self.webhook_key:
                print("企业微信配置加载成功")
                self.wechat_loaded = True
            else:
                print("企业微信配置不完整")
                self.wechat_loaded = False
            
            # 验证默认通知配置
            if self.default_ext_notify:
                if self.default_ext_notify not in ['wechat', 'telegram']:
                    print(f"警告：Default_ExtNotify配置无效: {self.default_ext_notify}，应为'Wechat'或'Telegram'")
                    self.default_ext_notify = None
                else:
                    print(f"默认外部通知平台: {self.default_ext_notify}")
            
            # 如果没有设置默认平台，自动选择一个可用的
            if not self.default_ext_notify:
                if self.wechat_loaded:
                    self.default_ext_notify = 'wechat'
                    print("自动选择企业微信作为默认通知平台")
                elif self.telegram_loaded:
                    self.default_ext_notify = 'telegram'
                    print("自动选择Telegram作为默认通知平台")
                else:
                    print("警告：没有可用的外部通知平台")
                
            return self.telegram_loaded or self.wechat_loaded
                
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return False
    
    def get_telegram_config(self):
        """获取Telegram配置"""
        return self.bot_token, self.chat_id
    
    def get_wechat_config(self):
        """获取企业微信配置"""
        return self.webhook_key
    
    def get_default_ext_notify(self):
        """获取默认外部通知平台"""
        return self.default_ext_notify
    
    def get_available_notifiers(self):
        """获取所有可用的通知平台"""
        available = []
        if self.is_telegram_configured():
            available.append('telegram')
        if self.is_wechat_configured():
            available.append('wechat')
        return available
    
    def set_telegram_config(self, bot_token, chat_id):
        """手动设置Telegram配置"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_loaded = True
        print(f"已手动设置Telegram配置")
    
    def set_wechat_config(self, webhook_key):
        """手动设置企业微信配置"""
        self.webhook_key = webhook_key
        self.wechat_loaded = True
        print(f"已手动设置企业微信配置")
    
    def set_default_ext_notify(self, platform):
        """手动设置默认通知平台"""
        platform = platform.lower()
        if platform in ['wechat', 'telegram']:
            self.default_ext_notify = platform
            print(f"已设置默认通知平台: {platform}")
        else:
            print(f"无效的通知平台: {platform}")
    
    def is_telegram_configured(self):
        """检查Telegram是否已配置"""
        return self.telegram_loaded and self.bot_token and self.chat_id
    
    def is_wechat_configured(self):
        """检查企业微信是否已配置"""
        return self.wechat_loaded and self.webhook_key

# 全局配置实例
app_config = Config()

def load_config(config_path=None):
    """加载配置文件"""
    return app_config.load_config(config_path)

def get_telegram_config():
    """获取Telegram配置"""
    return app_config.get_telegram_config()

def get_wechat_config():
    """获取企业微信配置"""
    return app_config.get_wechat_config()

def get_default_ext_notify():
    """获取默认外部通知平台"""
    return app_config.get_default_ext_notify()

def get_available_notifiers():
    """获取所有可用的通知平台"""
    return app_config.get_available_notifiers()

def set_telegram_config(bot_token, chat_id):
    """手动设置Telegram配置"""
    return app_config.set_telegram_config(bot_token, chat_id)

def set_wechat_config(webhook_key):
    """手动设置企业微信配置"""
    return app_config.set_wechat_config(webhook_key)

def set_default_ext_notify(platform):
    """手动设置默认通知平台"""
    return app_config.set_default_ext_notify(platform)

def is_telegram_configured():
    """检查Telegram是否已配置"""
    return app_config.is_telegram_configured()

def is_wechat_configured():
    """检查企业微信是否已配置"""
    return app_config.is_wechat_configured()