from .include import *
import json
import requests

# Load config.py
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
from config import (get_telegram_config, is_telegram_configured, 
                   get_wechat_config, is_wechat_configured,
                   get_default_ext_notify, get_available_notifiers)

#######################################################################################################################################################################################
################################################################################ Part I : Registration ################################################################################
#######################################################################################################################################################################################

class TelegramNotifier:
    """
    Telegram通知器
    """
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message):
        """发送消息到Telegram"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                MaaLog_Debug(f"Telegram消息发送成功: {message}")
                return True
            else:
                MaaLog_Debug(f"Telegram消息发送失败: {response.text}")
                return False
        except Exception as e:
            MaaLog_Debug(f"发送Telegram消息时出错: {e}")
            return False

class WeChatWorkNotifier:
    """
    企业微信通知器
    """
    def __init__(self, webhook_key):
        self.webhook_key = webhook_key
        self.webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_key}"
    
    def send_message(self, message, msgtype="text"):
        """发送消息到企业微信"""
        # 构造消息体
        if msgtype == "text":
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
        elif msgtype == "markdown":
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": message
                }
            }
        else:
            MaaLog_Debug(f"不支持的消息类型: {msgtype}")
            return False
        
        try:
            # 发送POST请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    MaaLog_Debug(f"企业微信消息发送成功: {message}")
                    return True
                else:
                    MaaLog_Debug(f"企业微信消息发送失败: {result.get('errmsg', '未知错误')}")
                    return False
            else:
                MaaLog_Debug(f"企业微信HTTP请求失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            MaaLog_Debug(f"发送企业微信消息时出错: {e}")
            return False

class ParametricBaseAction(CustomAction):
    """
    参数化动作基类
    提供通用的参数解析、处理和格式化功能
    """
    
    def __init__(self):
        super().__init__()
        self.action_name = self.__class__.__name__
    
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        基类run方法，处理通用逻辑
        """
        try:
            # 从custom_action_param获取参数
            param = argv.custom_action_param
            
            # 解析参数
            parsed_param = self._parse_param(param)
            
            # 处理参数化消息
            result = self._handle_parametric_message(parsed_param)
            
            return CustomAction.RunResult(success=result)
            
        except Exception as e:
            MaaLog_Debug(f"{self.action_name}执行异常: {e}")
            import traceback
            MaaLog_Debug(f"异常堆栈: {traceback.format_exc()}")
            return CustomAction.RunResult(success=False)
    
    def _parse_param(self, param):
        """
        解析参数，支持字符串、JSON和字典格式
        """
        # 无param：返回None
        if not param:
            MaaLog_Debug(f"{self.action_name}: 无参数，使用默认处理")
            return None
        
        # 调试：输出param的类型和内容
        MaaLog_Debug(f"{self.action_name} param类型: {type(param)}, 内容: {param}")
        
        # 尝试解析JSON字符串
        if isinstance(param, str):
            try:
                # 尝试将字符串解析为JSON
                parsed_param = json.loads(param)
                MaaLog_Debug(f"{self.action_name}: 成功解析JSON，类型: {type(parsed_param)}")
                return parsed_param
            except json.JSONDecodeError:
                # 如果不是JSON，直接返回字符串
                MaaLog_Debug(f"{self.action_name}: 非JSON字符串，直接使用")
                return param
        
        # 字典或其他类型直接返回
        return param
    
    def _process_parameters(self, parameters: dict) -> dict:
        """
        处理特殊参数，支持动态值
        """
        global Task_Counter
        
        processed = {}
        
        for key, value in parameters.items():
            MaaLog_Debug(f"{self.action_name}处理参数 {key}: {value} (类型: {type(value)})")
            
            if isinstance(value, str):
                # 处理特殊占位符
                if value == "{Task_Counter}":
                    processed[key] = Task_Counter
                    MaaLog_Debug(f"{self.action_name}替换 {key} = {Task_Counter}")
                elif value == "{increment_Task_Counter}":
                    Task_Counter += 1
                    processed[key] = Task_Counter
                    MaaLog_Debug(f"{self.action_name}递增并替换 {key} = {Task_Counter}")
                else:
                    processed[key] = value
            else:
                processed[key] = value
        
        return processed
    
    def _format_message(self, message_template: str, parameters: dict) -> str:
        """
        格式化消息模板
        """
        try:
            # 处理特殊参数
            processed_params = self._process_parameters(parameters)
            MaaLog_Debug(f"{self.action_name}处理后的参数: {processed_params}")
            
            # 格式化消息
            formatted_message = message_template.format(**processed_params)
            MaaLog_Debug(f"{self.action_name}格式化后的消息: {formatted_message}")
            return formatted_message
        except KeyError as e:
            MaaLog_Debug(f"{self.action_name}消息模板格式化失败，缺少参数: {e}")
            return message_template
        except Exception as e:
            MaaLog_Debug(f"{self.action_name}消息格式化异常: {e}")
            return message_template
    
    def _handle_parametric_message(self, parsed_param):
        """
        处理参数化消息的通用逻辑
        子类可以重写此方法来自定义处理逻辑
        """
        # 无参数情况
        if parsed_param is None:
            return self._handle_default_message()
        
        # 字符串情况：直接处理
        if isinstance(parsed_param, str):
            return self._handle_string_message(parsed_param)
        
        # 字典情况：参数化处理
        if isinstance(parsed_param, dict):
            return self._handle_dict_message(parsed_param)
        
        # 其他类型：转字符串处理
        return self._handle_string_message(str(parsed_param))
    
    # 抽象方法，子类必须实现
    def _handle_default_message(self):
        """处理默认消息，子类必须实现"""
        raise NotImplementedError("子类必须实现 _handle_default_message 方法")
    
    def _handle_string_message(self, message: str):
        """处理字符串消息，子类必须实现"""
        raise NotImplementedError("子类必须实现 _handle_string_message 方法")
    
    def _handle_dict_message(self, param_dict: dict):
        """处理字典参数消息，子类必须实现"""
        raise NotImplementedError("子类必须实现 _handle_dict_message 方法")

@AgentServer.custom_action("parametric_log")
class ParametricLogAction(ParametricBaseAction):
    """
    支持从custom_action_param中读取日志消息模板和参数
    """
    
    def _handle_default_message(self):
        """处理默认消息"""
        MaaLog_Info("默认日志消息")
        return True
    
    def _handle_string_message(self, message: str):
        """处理字符串消息"""
        MaaLog_Info(message)
        return True
    
    def _handle_dict_message(self, param_dict: dict):
        """处理字典参数消息"""
        log_type = param_dict.get('type', 'info')
        message_template = param_dict.get('message', '默认日志消息')
        parameters = param_dict.get('parameters', {})
        
        MaaLog_Debug(f"开始处理参数化日志 - 类型: {log_type}, 模板: {message_template}, 参数: {parameters}")
        
        # 格式化消息
        formatted_message = self._format_message(message_template, parameters)
        
        # 输出日志
        if log_type.lower() == 'debug':
            MaaLog_Debug(formatted_message)
        else:
            MaaLog_Info(formatted_message)
        
        return True

@AgentServer.custom_action("parametric_telegram")
class ParametricTelegramAction(ParametricBaseAction):
    """
    支持从custom_action_param中读取消息模板和参数，并发送到Telegram
    """
    
    def __init__(self):
        super().__init__()
        self.notifier = None
    
    def _get_notifier(self):
        """获取Telegram通知器"""
        if self.notifier is None:
            bot_token, chat_id = get_telegram_config()
            if not bot_token or not chat_id:
                MaaLog_Debug("Telegram配置未设置，无法发送消息")
                return None
            self.notifier = TelegramNotifier(bot_token, chat_id)
        return self.notifier
    
    def _handle_default_message(self):
        """处理默认消息"""
        notifier = self._get_notifier()
        if not notifier:
            return False
        return notifier.send_message("默认Telegram消息")
    
    def _handle_string_message(self, message: str):
        """处理字符串消息"""
        notifier = self._get_notifier()
        if not notifier:
            return False
        return notifier.send_message(message)
    
    def _handle_dict_message(self, param_dict: dict):
        """处理字典参数消息"""
        notifier = self._get_notifier()
        if not notifier:
            return False
        
        message_template = param_dict.get('message', '默认Telegram消息')
        parameters = param_dict.get('parameters', {})
        
        MaaLog_Debug(f"开始处理参数化Telegram消息 - 模板: {message_template}, 参数: {parameters}")
        
        # 格式化消息
        formatted_message = self._format_message(message_template, parameters)
        
        # 发送到Telegram
        return notifier.send_message(formatted_message)

@AgentServer.custom_action("parametric_wechat")
class ParametricWeChatAction(ParametricBaseAction):
    """
    支持从custom_action_param中读取消息模板和参数，并发送到企业微信
    """
    
    def __init__(self):
        super().__init__()
        self.notifier = None
    
    def _get_notifier(self):
        """获取企业微信通知器"""
        if self.notifier is None:
            webhook_key = get_wechat_config()
            if not webhook_key:
                MaaLog_Debug("企业微信配置未设置，无法发送消息")
                return None
            self.notifier = WeChatWorkNotifier(webhook_key)
        return self.notifier
    
    def _handle_default_message(self):
        """处理默认消息"""
        notifier = self._get_notifier()
        if not notifier:
            return False
        return notifier.send_message("默认企业微信消息")
    
    def _handle_string_message(self, message: str):
        """处理字符串消息"""
        notifier = self._get_notifier()
        if not notifier:
            return False
        return notifier.send_message(message)
    
    def _handle_dict_message(self, param_dict: dict):
        """处理字典参数消息"""
        notifier = self._get_notifier()
        if not notifier:
            return False
        
        message_template = param_dict.get('message', '默认企业微信消息')
        parameters = param_dict.get('parameters', {})
        msgtype = param_dict.get('msgtype', 'text')  # 支持消息类型设置
        
        MaaLog_Debug(f"开始处理参数化企业微信消息 - 模板: {message_template}, 参数: {parameters}, 类型: {msgtype}")
        
        # 格式化消息
        formatted_message = self._format_message(message_template, parameters)
        
        # 发送到企业微信
        return notifier.send_message(formatted_message, msgtype)

@AgentServer.custom_action("parametric_extnotify")
class ParametricExtNotifyAction(ParametricBaseAction):
    """
    智能外部通知动作
    根据配置自动选择Telegram或企业微信发送消息
    """
    
    def __init__(self):
        super().__init__()
        self.telegram_notifier = None
        self.wechat_notifier = None
    
    def _get_telegram_notifier(self):
        """获取Telegram通知器"""
        if self.telegram_notifier is None:
            bot_token, chat_id = get_telegram_config()
            if bot_token and chat_id:
                self.telegram_notifier = TelegramNotifier(bot_token, chat_id)
        return self.telegram_notifier
    
    def _get_wechat_notifier(self):
        """获取企业微信通知器"""
        if self.wechat_notifier is None:
            webhook_key = get_wechat_config()
            if webhook_key:
                self.wechat_notifier = WeChatWorkNotifier(webhook_key)
        return self.wechat_notifier
    
    def _send_message_with_fallback(self, message, msgtype="text", preferred_platform=None):
        """
        发送消息，支持自动降级
        """
        # 获取默认平台和可用平台
        default_platform = preferred_platform or get_default_ext_notify()
        available_platforms = get_available_notifiers()
        
        MaaLog_Debug(f"智能通知 - 默认平台: {default_platform}, 可用平台: {available_platforms}")
        
        if not available_platforms:
            MaaLog_Debug("智能通知失败: 没有可用的通知平台")
            return False
        
        # 构建尝试顺序
        try_order = []
        if default_platform and default_platform in available_platforms:
            try_order.append(default_platform)
        
        # 添加其他可用平台作为备选
        for platform in available_platforms:
            if platform not in try_order:
                try_order.append(platform)
        
        MaaLog_Debug(f"智能通知尝试顺序: {try_order}")
        
        # 按顺序尝试发送
        for platform in try_order:
            try:
                if platform == 'telegram':
                    notifier = self._get_telegram_notifier()
                    if notifier:
                        MaaLog_Debug(f"尝试通过Telegram发送消息")
                        if notifier.send_message(message):
                            MaaLog_Debug(f"智能通知成功: 使用Telegram发送")
                            return True
                        else:
                            MaaLog_Debug(f"Telegram发送失败，尝试下一个平台")
                elif platform == 'wechat':
                    notifier = self._get_wechat_notifier()
                    if notifier:
                        MaaLog_Debug(f"尝试通过企业微信发送消息")
                        if notifier.send_message(message, msgtype):
                            MaaLog_Debug(f"智能通知成功: 使用企业微信发送")
                            return True
                        else:
                            MaaLog_Debug(f"企业微信发送失败，尝试下一个平台")
            except Exception as e:
                MaaLog_Debug(f"{platform}发送异常: {e}，尝试下一个平台")
                continue
        
        MaaLog_Debug("智能通知失败: 所有平台都无法发送消息")
        return False
    
    def _handle_default_message(self):
        """处理默认消息"""
        return self._send_message_with_fallback("默认智能通知消息")
    
    def _handle_string_message(self, message: str):
        """处理字符串消息"""
        return self._send_message_with_fallback(message)
    
    def _handle_dict_message(self, param_dict: dict):
        """处理字典参数消息"""
        message_template = param_dict.get('message', '默认智能通知消息')
        parameters = param_dict.get('parameters', {})
        msgtype = param_dict.get('msgtype', 'text')
        preferred_platform = param_dict.get('platform', None)
        
        MaaLog_Debug(f"开始处理参数化智能通知消息 - 模板: {message_template}, 参数: {parameters}, 类型: {msgtype}, 首选平台: {preferred_platform}")
        
        # 格式化消息
        formatted_message = self._format_message(message_template, parameters)
        
        # 发送消息
        return self._send_message_with_fallback(formatted_message, msgtype, preferred_platform)

##########################################################################################################################################################################################
################################################################################ Part II : Implementation ################################################################################
##########################################################################################################################################################################################

def MaaLog_Debug(message):
    """调试日志输出"""
    if Enable_MaaLog_Debug:
        print(f"[DEBUG] {message}")

def MaaLog_Info(message):
    """信息日志输出"""
    if Enable_MaaLog_Info:
        print(f"[INFO] {message}")

def set_debug_log(enabled):
    """设置调试日志开关"""
    global Enable_MaaLog_Debug
    Enable_MaaLog_Debug = 1 if enabled else 0

def set_info_log(enabled):
    """设置信息日志开关"""
    global Enable_MaaLog_Info
    Enable_MaaLog_Info = 1 if enabled else 0

def get_Task_Counter():
    """获取当前任务运行次数"""
    global Task_Counter
    return Task_Counter

def reset_Task_Counter():
    """重置任务运行次数"""
    global Task_Counter
    Task_Counter = 0