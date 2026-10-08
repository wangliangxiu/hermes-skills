# Git 中文 Windows 用户名路径问题

## 症状

Windows 用户名为中文（如「使用者」），git-bash 中 `$HOME` 显示乱码：

```
$ echo $HOME
/c/Users/������
```

导致 `git config --global user.name` 和 `git config --global user.email` 返回空（退出码 1），因为 git 找不到正确的 `.gitconfig` 路径。

## 根因

git-bash（MSYS2 环境）使用 `getpwuid` 或 `/etc/passwd` 获取 home 目录。当中文用户名在 MSYS2 的字符编码转换中出现问题时，`$HOME` 指向了一个乱码路径，而实际的 `.gitconfig` 在 `C:\Users\使用者\.gitconfig`。

## 解决方案（3选1）

### 方案 A：直接写配置文件（推荐）

```python
# 用 write_file 直接写入正确路径
write_file("C:\\Users\\使用者\\.gitconfig", """[user]
	name = zhuder
	email = your@email.com
""")
```

### 方案 B：显式指定 HOME 来运行 git config

```bash
HOME="/c/Users/使用者" git config --global user.name "zhuder"
HOME="/c/Users/使用者" git config --global user.email "your@email.com"
```

### 方案 C：验证配置是否生效

```bash
HOME="/c/Users/使用者" git config --global user.name
# 应输出用户名
HOME="/c/Users/使用者" git config --global user.email
# 应输出邮箱
```

## 注意事项

- 此问题仅影响 git-bash 终端中的 `git config --global` 命令
- VS Code、Git GUI 等其他工具能正确读取 `C:\Users\中文用户名\.gitconfig`，不受影响
- Git 本身的 clone、commit、push 等功能正常——只有配置读取受影响
- 如果用户自己不在终端里配 git config，甚至不会意识到有问题

## 相关链接

- https://stackoverflow.com/questions/61511757/git-bash-home-path-issue-with-chinese-username
