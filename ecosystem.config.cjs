module.exports = {
  apps: [
    {
      name: "autosecure-bot",
      cwd: "/root/autosecure",
      script: ".venv/bin/python",
      args: "-u bot.py",
      env: {
        PYTHONUNBUFFERED: "1",
      },
      autorestart: true,
      max_restarts: 10,
    },
  ],
};
