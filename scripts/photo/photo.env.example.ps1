# 复制成 photo.env.ps1 后填你自己的值（photo.env.ps1 已被 .gitignore 忽略，不会进库）
# 例：Copy-Item photo.env.example.ps1 photo.env.ps1

# 中转站 / 自建网关的 OpenAI 兼容前缀，一般以 /v1 结尾
$env:PHOTO_BASE_URL = 'https://your-relay.example.com/v1'

# 你的 key（只写在本机这个文件里，不要贴进聊天、不要提交）
$env:PHOTO_API_KEY = 'sk-xxxxxxxxxxxxxxxx'

# 可选：把常用模型固定下来，避免每次敲 -VisionModel / -ImageModel
# $env:PHOTO_VISION_MODEL = 'gpt-4o'
# $env:PHOTO_IMAGE_MODEL  = 'gpt-image-1'
