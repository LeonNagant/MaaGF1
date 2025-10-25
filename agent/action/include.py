# 标准库导入
import time
import ctypes
import sys
import os
import traceback
import json
import re

# Win32相关导入
import win32con
import win32gui
import win32process
import win32api
import win32ui
from ctypes import windll, wintypes, byref, sizeof

# 图像处理导入
from PIL import Image, ImageGrab
import numpy as np

# MaaFramework相关导入
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

#################### 全局变量 ####################

# 任务计数器
Task_Counter = 0

#################### 日志控制开关 ####################

Enable_MaaLog_Debug = 1
Enable_MaaLog_Info = 1

#################### Telegram配置 ####################

# Telegram配置变量
Bot_Token = None
Chat_ID = None