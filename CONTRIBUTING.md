# 贡献指南

感谢你对视频去重工具的关注！欢迎提交代码、报告问题或提出改进建议。

## 🐛 报告问题

1. 在 [Issues](https://github.com/hnwxwt/video-dedup/issues) 中搜索是否已有类似问题
2. 如果没有，创建新的 Issue，包含：
   - 清晰的标题
   - 复现步骤
   - 预期行为 vs 实际行为
   - 系统环境（Python版本、操作系统）
   - 错误日志或截图

## 💡 提交功能请求

1. 描述你想要的功能
2. 说明为什么需要这个功能
3. 提供可能的实现思路（可选）

## 🔧 提交代码

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/hnwxwt/video-dedup.git
cd video-dedup

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 代码规范

- 遵循 PEP 8 编码规范
- 使用有意义的变量名和函数名
- 添加必要的注释
- 保持函数职责单一

### 提交流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 Commit 消息规范

使用清晰的 commit 消息：

```
类型: 简短描述

详细说明（可选）

- 修改点1
- 修改点2

相关 Issue: #123
```

类型包括：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

## 🧪 测试

提交前请确保：
- 代码能正常运行
- 没有明显的bug
- 更新了相关文档

## 📄 许可证

提交代码即表示你同意将代码以 MIT 许可证发布。

---

再次感谢你的贡献！🎉
