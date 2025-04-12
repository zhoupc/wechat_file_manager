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