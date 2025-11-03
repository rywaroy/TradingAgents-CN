# 使用官方Python镜像替代GitHub Container Registry
FROM python:3.10-slim-bookworm

# 安装uv包管理器 (保留，以防万一)
RUN pip install --timeout=100 -i https://repo.huaweicloud.com/repository/pypi/simple uv

WORKDIR /app

RUN mkdir -p /app/data /app/logs

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# --- APT-GET 源修改 ---
# 彻底删除默认的 debian.sources 并使用完整的华为云源
RUN rm -f /etc/apt/sources.list.d/debian.sources \
    && echo 'deb https://mirrors.huaweicloud.com/debian/ bookworm main contrib non-free non-free-firmware' > /etc/apt/sources.list \
    && echo 'deb https://mirrors.huaweicloud.com/debian/ bookworm-updates main contrib non-free non-free-firmware' >> /etc/apt/sources.list \
    && echo 'deb https://mirrors.huaweicloud.com/debian-security/ bookworm-security main contrib non-free non-free-firmware' >> /etc/apt/sources.list
# --- 修改结束 ---

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wkhtmltopdf \
    xvfb \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-liberation \
    pandoc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 启动Xvfb虚拟显示器
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1024x768x24 -ac +extension GLX &\nexport DISPLAY=:99\nexec "$@"' > /usr/local/bin/start-xvfb.sh \
    && chmod +x /usr/local/bin/start-xvfb.sh

# --- 依赖安装修改 ---
# 复制 lock 文件，这是修复所有问题的关键
COPY requirements.txt .
COPY requirements-lock.txt .

# 关键修复：从 lock 文件中删除 Windows 专属的 pywin32 包
RUN sed -i '/pywin32/d' requirements-lock.txt

# 直接使用 lock 文件安装
# 这会跳过所有依赖解析，并确保安装已知可用的版本组合
RUN pip install \
    --no-cache-dir \
    --timeout=100 \
    -r requirements-lock.txt \
    -i https://repo.huaweicloud.com/repository/pypi/simple
# --- 修改结束 ---


# 复制日志配置文件
COPY config/ ./config/

COPY . .

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "web/app.py", "--server.address=0.0.0.0", "--server.port=8501"]

