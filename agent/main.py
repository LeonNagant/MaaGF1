import sys
import os
import traceback
import time
import uuid

def get_executable_dir():
    """获取可执行文件所在目录"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        return os.path.dirname(os.path.abspath(__file__))

def get_project_root():
    """获取项目根目录"""
    current_dir = get_executable_dir()
    
    if getattr(sys, 'frozen', False):
        # 打包后的exe环境：从 PROJECT_DIR/agent/dist/ 回到 PROJECT_DIR/
        return os.path.dirname(os.path.dirname(current_dir))
    else:
        # 开发环境：从 PROJECT_DIR/agent/ 回到 PROJECT_DIR/
        return os.path.dirname(current_dir)

def setup_dll_path():
    """设置DLL路径"""
    current_dir = get_executable_dir()
    project_root = get_project_root()
    
    print(f"当前目录: {current_dir}")
    print(f"项目根目录: {project_root}")
    print(f"运行环境: {'打包exe' if getattr(sys, 'frozen', False) else '开发环境'}")
    
    # DLL在项目根目录
    dll_dir = project_root
    
    # 检查关键DLL文件是否存在
    key_dlls = [
        "MaaFramework.dll",
        "MaaAgentServer.dll", 
        "MaaToolkit.dll"
    ]
    
    dll_exists = True
    for dll_name in key_dlls:
        dll_path = os.path.join(dll_dir, dll_name)
        if os.path.exists(dll_path):
            print(f"✅ 找到 {dll_name}: {dll_path}")
        else:
            print(f"❌ 未找到 {dll_name}: {dll_path}")
            dll_exists = False
    
    if not dll_exists:
        print("❌ 关键DLL文件缺失，程序无法运行")
        sys.exit(1)
    
    # 设置MAAFW_BINARY_PATH环境变量
    os.environ["MAAFW_BINARY_PATH"] = dll_dir
    print(f"设置 MAAFW_BINARY_PATH: {dll_dir}")
    
    # 将DLL目录添加到PATH的最前面
    old_path = os.environ.get("PATH", "")
    new_path = dll_dir + os.pathsep + old_path
    os.environ["PATH"] = new_path
    print(f"已将DLL目录添加到PATH: {dll_dir}")
    
    # 设置其他环境变量
    os.environ["MAA_LIBRARY_PATH"] = dll_dir
    
    return dll_dir, project_root

def generate_socket_id():
    """生成一个唯一的socket_id"""
    return f"maa_agent_{uuid.uuid4().hex[:8]}"

# 在导入MaaFramework之前设置DLL路径和环境变量
print("开始设置DLL环境...")
dll_dir, project_root = setup_dll_path()
print("DLL环境设置完成")

# 现在导入maa模块
try:
    print("开始导入 MaaFramework 模块...")
    from maa.agent.agent_server import AgentServer
    from maa.toolkit import Toolkit
    print("✅ MaaFramework 模块导入成功")
except Exception as e:
    print(f"❌ MaaFramework 模块导入失败: {e}")
    print("详细错误信息:")
    traceback.print_exc()
    
    print(f"\n调试信息:")
    print(f"MAAFW_BINARY_PATH: {os.environ.get('MAAFW_BINARY_PATH', 'Not set')}")
    print(f"PATH前几个目录: {os.environ.get('PATH', '')[:200]}...")
    sys.exit(1)

# 导入自定义模块
try:
    print("开始导入自定义模块...")
    import my_reco
    from action import input, log
    from server import server
    print("✅ 自定义模块导入成功")
    
except Exception as e:
    print(f"❌ 自定义模块导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

# 加载配置文件
try:
    print("开始加载配置文件...")
    
    # 修正配置文件路径
    if getattr(sys, 'frozen', False):
        # 打包环境：配置文件在项目根目录的agent子目录中
        config_path = os.path.join(project_root, "agent", "agent.conf")
    else:
        # 开发环境：配置文件在当前目录
        config_path = os.path.join(get_executable_dir(), "agent.conf")
    
    print(f"配置文件路径: {config_path}")
    
    from config import load_config
    load_config(config_path)
    print("配置文件加载完成")
    
except Exception as e:
    print(f"❌ 配置文件加载失败: {e}")
    traceback.print_exc()
    sys.exit(1)

def main():
    custom_server = None
    
    try:
        print("开始初始化 MaaFramework...")
        Toolkit.init_option(dll_dir)
        print("MaaFramework 初始化完成")

        # 处理socket_id参数
        print(f"命令行参数: {sys.argv}")
        
        if len(sys.argv) >= 2:
            # 如果提供了参数，使用第一个参数作为socket_id
            socket_id = sys.argv[1]
            print(f"使用命令行提供的socket_id: {socket_id}")
        else:
            # 如果没有提供参数，自动生成一个socket_id
            socket_id = generate_socket_id()
            print(f"自动生成socket_id: {socket_id}")
        
        print(f"最终使用的socket_id: {socket_id}")

        print("开始启动 AgentServer...")
        AgentServer.start_up(socket_id)
        print("AgentServer 启动成功")
        
        # 等待AgentServer完全启动
        print("等待 AgentServer 完全启动...")
        time.sleep(2)
        print("AgentServer 启动等待完成")
        
        # 启动CustomServer后台服务
        print("开始启动 CustomServer...")
        custom_server = server.get_custom_server()
        custom_server.start()
        print("CustomServer 启动成功")
        
        print("开始等待连接...")
        
        # AgentServer.join() 会阻塞直到连接结束
        AgentServer.join()
        print("AgentServer 连接结束")
        
        # 清理资源
        print("开始清理资源...")
        if custom_server:
            custom_server.stop()
        AgentServer.shut_down()
        print("所有服务关闭完成")

    except Exception as e:
        print(f"服务启动失败: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        
        # 输出调试信息
        print(f"\n调试信息:")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"MAAFW_BINARY_PATH: {os.environ.get('MAAFW_BINARY_PATH', 'Not set')}")
        print(f"命令行参数: {sys.argv}")
        
        # 确保在出错时也能清理资源
        try:
            if custom_server:
                custom_server.stop()
        except:
            pass
        
        try:
            AgentServer.shut_down()
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()