# AY-2025

项目运行说明

基础要求：已安装 `python`（建议 Python 3.8+）。

快速开始：

1. 创建并激活虚拟环境（推荐）

```bash
python -m venv .venv
source .venv/bin/activate
```

2. 安装依赖

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. 启动开发服务器（最简单）

```bash
python /workspaces/AY-2025/app.py
```

4. 使用 Flask CLI（带热重载）

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=127.0.0.1 --port=5000
```

5. 在容器或远程可访问时监听所有接口

```bash
flask run --host=0.0.0.0 --port=5000
```

后台运行（将输出写入日志）：

```bash
python /workspaces/AY-2025/app.py &> flask.log &
tail -f flask.log
```

生产环境提示：使用 WSGI 服务器（示例使用 `gunicorn`）

```bash
python -m pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

常见问题
- **ModuleNotFoundError: No module named 'flask'**：激活虚拟环境并运行 `pip install -r requirements.txt`。
- **模板找不到**：确认 `templates/index.html` 存在。
- **端口被占用**：换端口或 `lsof -i :5000` 查找占用进程。

如果你需要，我可以：
- 帮你在当前容器中启动并验证应用（并贴日志）；
- 添加 `Dockerfile` 或 `Procfile` 来辅助部署。
