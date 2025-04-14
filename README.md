# WeChat 文件管理器

一个用于 MacOS 系统的微信文件管理工具，通过创建集中存储和符号链接来实现文件去重和空间节省。

## 主要功能

- 使用 MD5 哈希进行文件去重
- 为微信媒体文件创建集中存储
- 使用符号链接保持原始文件结构
- 可配置文件大小限制和跳过模式
- 可选择保留原始文件

## 安装方法

```bash
pip install git+https://github.com/zhoupc/wechat_file_manager.git
```

## 使用方法
1. 运行 `wfm init` 命令初始化配置文件

这一条命令会在主目录下创建一个名为`cofnig_wechat_file_manager.yaml` 的文件，你可以根据自己的实际情况进行调整

```yaml 
paths:
  storage: ~/Documents/WeChatStorage  # 集中存储路径
  wechat: ~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/2.0b4.0.9/cbff6dbadbdf84e918bfcc7477c75023/Message/MessageTemp/  # 微信文件路径, 你可以通过在任意聊天窗口中选择一个文件/照片/视频，查看其路径， 向上找几层就可以得到
settings:
  min_file_size: 1  # 最小文件大小，单位为MB
  preserve_originals: true # 是否保留原始文件，如果为false，会将文件替换为符号链接
  skip_patterns:    # 跳过模式，用于跳过某些文件夹或文件
  - pic_thumb
  - .DS_Store
  target_folders:   # 只对以下文件夹进行管理 
  - Audio
  - File
  - Image
  - Video
state:  
  last_run: '2020-00-00T00:00:00.000000'  # 上次运行时间， 每次只检索该时间之后的文件
```

2. 运行 `wfm run` 命令开始文件管理

## 联系
zhoupc1988@gmail.com