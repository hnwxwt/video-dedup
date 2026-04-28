# 双仓库推送配置指南

## 📋 当前配置

- **Gitee**: https://gitee.com/vXiaoTong/video-dedup (origin)
- **GitHub**: https://github.com/hnwxwt/video-dedup (github)

## 🔑 配置访问凭证

### 方法1：使用HTTPS + Personal Access Token（推荐）

#### Gitee 配置步骤

1. **获取Gitee私人令牌**
   - 访问: https://gitee.com/profile/personal_access_tokens
   - 点击"生成新令牌"
   - 勾选权限：`projects` (项目)
   - 生成后复制令牌（只显示一次）

2. **配置Git凭据**
   ```bash
   # 方式A：每次推送时输入用户名和令牌
   git push origin main
   # 用户名: 你的Gitee用户名
   # 密码: 刚才生成的令牌
   
   # 方式B：保存凭据到Git Credential Manager
   git config --global credential.helper manager-core
   ```

3. **测试推送**
   ```bash
   git push origin main
   ```

#### GitHub 配置步骤

1. **获取GitHub Personal Access Token**
   - 访问: https://github.com/settings/tokens
   - 点击"Generate new token (classic)"
   - 勾选权限：`repo` (完整仓库访问)
   - 生成后复制令牌

2. **测试推送**
   ```bash
   git push github main
   ```

### 方法2：使用SSH密钥（更安全）

#### Gitee SSH配置

1. **生成SSH密钥**（如果还没有）
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   ```

2. **添加公钥到Gitee**
   - 复制公钥内容：`cat ~/.ssh/id_ed25519.pub`
   - 访问: https://gitee.com/profile/sshkeys
   - 点击"添加公钥"，粘贴内容

3. **修改远程URL为SSH**
   ```bash
   git remote set-url origin git@gitee.com:vXiaoTong/video-dedup.git
   ```

#### GitHub SSH配置

1. **添加公钥到GitHub**
   - 访问: https://github.com/settings/keys
   - 点击"New SSH key"，粘贴公钥内容

2. **修改远程URL为SSH**
   ```bash
   git remote set-url github git@github.com:hnwxwt/video-dedup.git
   ```

3. **测试连接**
   ```bash
   ssh -T git@github.com
   ```

## 🚀 快速推送命令

### 推送到两个仓库

```bash
# 方法1：分别推送
git push origin main      # Gitee
git push github main      # GitHub

# 方法2：使用批处理脚本
.\push_all.bat

# 方法3：配置一个别名同时推送
git remote add all https://gitee.com/vXiaoTong/video-dedup.git
git remote set-url --add all https://github.com/hnwxwt/video-dedup.git
git push all main
```

### 查看远程仓库

```bash
git remote -v
```

应该显示：
```
github  https://github.com/hnwxwt/video-dedup.git (fetch)
github  https://github.com/hnwxwt/video-dedup.git (push)
origin  https://gitee.com/vXiaoTong/video-dedup.git (fetch)
origin  https://gitee.com/vXiaoTong/video-dedup.git (push)
```

## ⚠️ 常见问题

### 1. 认证失败

**错误**: `Authentication failed`

**解决**:
- 确认使用的是Personal Access Token而不是密码
- 检查令牌是否有足够的权限
- 重新配置Git凭据管理器

### 2. 推送被拒绝

**错误**: `rejected [non-fast-forward]`

**解决**:
```bash
# 先拉取远程更改
git pull origin main --rebase
git pull github main --rebase

# 再推送
git push origin main
git push github main
```

### 3. 分支不存在

**错误**: `src refspec main does not match any`

**解决**:
```bash
# 创建main分支
git branch -M main

# 推送
git push -u origin main
git push -u github main
```

## 💡 最佳实践

1. **优先推送到Gitee**（国内速度快）
2. **定期同步两个仓库**，保持一致性
3. **使用Token而非密码**，更安全且可撤销
4. **配置Credential Manager**，避免重复输入
5. **重要更新先测试**，确认无误后再双推

## 🔍 验证推送成功

推送完成后访问以下链接确认：
- Gitee: https://gitee.com/vXiaoTong/video-dedup
- GitHub: https://github.com/hnwxwt/video-dedup

检查：
- ✓ 文件列表完整
- ✓ README正确显示
- ✓ 提交历史正确
- ✓ 分支为main

---

**提示**: 首次推送可能需要较长时间，请耐心等待。
