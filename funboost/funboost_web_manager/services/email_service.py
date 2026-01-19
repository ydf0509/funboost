# -*- coding: utf-8 -*-
"""
邮件服务模块

提供邮件配置管理和邮件发送功能。
"""

import smtplib
import ssl
import secrets
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple, Dict, Any

from ..user_models import get_session, EmailConfig, PasswordResetToken


class EmailService:
    """邮件发送服务"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化邮件服务
        
        Args:
            db_url: 可选的数据库 URL
        """
        self.db_url = db_url
        self._config_cache = None
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """
        从数据库加载邮件配置
        
        Returns:
            Optional[Dict]: 邮件配置字典或None（未配置）
        """
        session = get_session(self.db_url)
        try:
            config = session.query(EmailConfig).first()
            if config:
                self._config_cache = {
                    'smtp_host': config.smtp_host,
                    'smtp_port': config.smtp_port,
                    'smtp_username': config.smtp_username,
                    'smtp_password': config.smtp_password,
                    'use_tls': config.use_tls,
                    'use_ssl': config.use_ssl,
                    'sender_name': config.sender_name,
                    'sender_email': config.sender_email
                }
                return self._config_cache
            return None
        finally:
            session.close()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存邮件配置到数据库
        
        Args:
            config: 邮件配置字典
            
        Returns:
            bool: 是否保存成功
        """
        session = get_session(self.db_url)
        try:
            # 查找现有配置
            email_config = session.query(EmailConfig).first()
            
            if email_config:
                # 更新现有配置
                email_config.smtp_host = config.get('smtp_host', '')
                email_config.smtp_port = config.get('smtp_port', 587)
                email_config.smtp_username = config.get('smtp_username')
                email_config.smtp_password = config.get('smtp_password')
                email_config.use_tls = config.get('use_tls', True)
                email_config.use_ssl = config.get('use_ssl', False)
                email_config.sender_name = config.get('sender_name')
                email_config.sender_email = config.get('sender_email', '')
            else:
                # 创建新配置
                email_config = EmailConfig(
                    smtp_host=config.get('smtp_host', ''),
                    smtp_port=config.get('smtp_port', 587),
                    smtp_username=config.get('smtp_username'),
                    smtp_password=config.get('smtp_password'),
                    use_tls=config.get('use_tls', True),
                    use_ssl=config.get('use_ssl', False),
                    sender_name=config.get('sender_name'),
                    sender_email=config.get('sender_email', '')
                )
                session.add(email_config)
            
            session.commit()
            
            # 清除缓存
            self._config_cache = None
            
            return True
            
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def send_password_reset_email(self, to_email: str, reset_link: str, 
                                 user_name: str = None) -> Tuple[bool, str]:
        """
        发送密码重置邮件
        
        Args:
            to_email: 收件人邮箱
            reset_link: 重置链接
            user_name: 用户名（可选）
            
        Returns:
            Tuple[bool, str]: (成功, 消息)
        """
        config = self.load_config()
        if not config:
            return False, "邮件服务未配置"
        
        subject = "密码重置请求"
        
        # HTML 邮件内容
        html_content = f"""
        <html>
        <body>
            <h2>密码重置请求</h2>
            <p>您好{f'，{user_name}' if user_name else ''}！</p>
            <p>我们收到了您的密码重置请求。请点击下面的链接重置您的密码：</p>
            <p><a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">重置密码</a></p>
            <p>或者复制以下链接到浏览器地址栏：</p>
            <p><code>{reset_link}</code></p>
            <p><strong>注意：</strong></p>
            <ul>
                <li>此链接将在30分钟后失效</li>
                <li>如果您没有请求重置密码，请忽略此邮件</li>
                <li>为了您的账户安全，请不要将此链接分享给他人</li>
            </ul>
            <p>如有疑问，请联系系统管理员。</p>
            <hr>
            <p><small>此邮件由系统自动发送，请勿回复。</small></p>
        </body>
        </html>
        """
        
        # 纯文本内容（备用）
        text_content = f"""
        密码重置请求
        
        您好{f'，{user_name}' if user_name else ''}！
        
        我们收到了您的密码重置请求。请复制以下链接到浏览器地址栏重置您的密码：
        
        {reset_link}
        
        注意：
        - 此链接将在30分钟后失效
        - 如果您没有请求重置密码，请忽略此邮件
        - 为了您的账户安全，请不要将此链接分享给他人
        
        如有疑问，请联系系统管理员。
        
        此邮件由系统自动发送，请勿回复。
        """
        
        return self._send_email(to_email, subject, text_content, html_content, config)
    
    def send_password_notification(self, to_email: str, new_password: str, 
                                  user_name: str = None) -> Tuple[bool, str]:
        """
        发送管理员重置密码通知邮件
        
        Args:
            to_email: 收件人邮箱
            new_password: 新密码
            user_name: 用户名（可选）
            
        Returns:
            Tuple[bool, str]: (成功, 消息)
        """
        config = self.load_config()
        if not config:
            return False, "邮件服务未配置"
        
        subject = "密码已重置"
        
        # HTML 邮件内容
        html_content = f"""
        <html>
        <body>
            <h2>密码已重置</h2>
            <p>您好{f'，{user_name}' if user_name else ''}！</p>
            <p>您的密码已由管理员重置。新的登录信息如下：</p>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p><strong>用户名：</strong>{user_name or '（请联系管理员确认）'}</p>
                <p><strong>新密码：</strong><code style="background-color: #e9ecef; padding: 2px 4px; border-radius: 3px;">{new_password}</code></p>
            </div>
            <p><strong>重要提醒：</strong></p>
            <ul>
                <li style="color: #dc3545;"><strong>请在首次登录后立即修改密码</strong></li>
                <li>为了您的账户安全，请不要将密码分享给他人</li>
                <li>建议使用包含大小写字母、数字和特殊字符的强密码</li>
            </ul>
            <p>如有疑问，请联系系统管理员。</p>
            <hr>
            <p><small>此邮件由系统自动发送，请勿回复。</small></p>
        </body>
        </html>
        """
        
        # 纯文本内容（备用）
        text_content = f"""
        密码已重置
        
        您好{f'，{user_name}' if user_name else ''}！
        
        您的密码已由管理员重置。新的登录信息如下：
        
        用户名：{user_name or '（请联系管理员确认）'}
        新密码：{new_password}
        
        重要提醒：
        - 请在首次登录后立即修改密码
        - 为了您的账户安全，请不要将密码分享给他人
        - 建议使用包含大小写字母、数字和特殊字符的强密码
        
        如有疑问，请联系系统管理员。
        
        此邮件由系统自动发送，请勿回复。
        """
        
        return self._send_email(to_email, subject, text_content, html_content, config)
    
    def send_test_email(self, to_email: str) -> Tuple[bool, str]:
        """
        发送测试邮件
        
        Args:
            to_email: 收件人邮箱
            
        Returns:
            Tuple[bool, str]: (成功, 消息)
        """
        config = self.load_config()
        if not config:
            return False, "邮件服务未配置"
        
        subject = "邮件服务测试"
        
        # HTML 邮件内容
        html_content = """
        <html>
        <body>
            <h2>邮件服务测试</h2>
            <p>这是一封测试邮件，用于验证邮件服务配置是否正确。</p>
            <p>如果您收到此邮件，说明邮件服务配置成功！</p>
            <div style="background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 15px 0;">
                <strong>✓ 邮件服务配置正常</strong>
            </div>
            <hr>
            <p><small>此邮件由系统自动发送，请勿回复。</small></p>
        </body>
        </html>
        """
        
        # 纯文本内容（备用）
        text_content = """
        邮件服务测试
        
        这是一封测试邮件，用于验证邮件服务配置是否正确。
        
        如果您收到此邮件，说明邮件服务配置成功！
        
        ✓ 邮件服务配置正常
        
        此邮件由系统自动发送，请勿回复。
        """
        
        return self._send_email(to_email, subject, text_content, html_content, config)
    
    def validate_config(self) -> Tuple[bool, str]:
        """
        验证邮件配置并提供诊断信息
        
        Returns:
            Tuple[bool, str]: (是否有效, 诊断信息)
        """
        config = self.load_config()
        if not config:
            return False, "邮件服务未配置"
        
        issues = []
        warnings = []
        
        # 检查必需字段
        if not config.get('smtp_host'):
            issues.append("SMTP服务器地址未配置")
        if not config.get('smtp_port'):
            issues.append("SMTP端口未配置")
        if not config.get('sender_email'):
            issues.append("发件人邮箱未配置")
        elif '@' not in config['sender_email']:
            issues.append("发件人邮箱格式无效")
        
        # 检查认证配置
        if not config.get('smtp_username') or not config.get('smtp_password'):
            warnings.append("未配置SMTP认证信息，某些服务器可能拒绝发送")
        
        # 检查发件人域名和SMTP服务器是否匹配
        if config.get('sender_email') and config.get('smtp_host'):
            sender_domain = config['sender_email'].split('@')[1].lower()
            smtp_host = config['smtp_host'].lower()
            
            # 常见的域名和SMTP服务器匹配检查
            domain_smtp_map = {
                'qq.com': ['smtp.qq.com'],
                'foxmail.com': ['smtp.qq.com'],
                'gmail.com': ['smtp.gmail.com'],
                '163.com': ['smtp.163.com'],
                '126.com': ['smtp.126.com'],
                'sina.com': ['smtp.sina.com'],
                'outlook.com': ['smtp-mail.outlook.com', 'smtp.office365.com'],
                'hotmail.com': ['smtp-mail.outlook.com', 'smtp.office365.com'],
            }
            
            if sender_domain in domain_smtp_map:
                expected_servers = domain_smtp_map[sender_domain]
                if not any(server in smtp_host for server in expected_servers):
                    warnings.append(
                        f"⚠️ 发件人域名({sender_domain})与SMTP服务器({smtp_host})不匹配！\n"
                        f"   建议使用: {', '.join(expected_servers)}\n"
                        f"   当前配置可能导致SPF/DKIM认证失败，邮件被拒收。"
                    )
        
        # 检查SSL/TLS配置
        if config.get('use_ssl') and config.get('use_tls'):
            warnings.append("同时启用了SSL和TLS，这可能导致连接问题")
        
        # 端口和加密方式匹配检查
        port = config.get('smtp_port')
        if port == 465 and not config.get('use_ssl'):
            warnings.append("端口465通常需要启用SSL")
        elif port == 587 and not config.get('use_tls'):
            warnings.append("端口587通常需要启用TLS")
        
        # 生成诊断报告
        if issues:
            return False, "配置错误：\n" + "\n".join(f"- {issue}" for issue in issues)
        
        if warnings:
            return True, "配置可用，但有以下建议：\n" + "\n".join(f"- {warning}" for warning in warnings)
        
        return True, "配置验证通过"
    
    def generate_email_verification_token(self, user_id: int, new_email: str) -> Optional[str]:
        """
        生成邮箱验证令牌
        
        Args:
            user_id: 用户ID
            new_email: 新邮箱地址
            
        Returns:
            Optional[str]: 验证令牌或None（失败）
        """
        session = get_session(self.db_url)
        try:
            # 生成唯一令牌
            token = secrets.token_urlsafe(32)
            
            # 设置过期时间（30分钟）
            expires_at = datetime.now() + timedelta(minutes=30)
            
            # 存储令牌（复用PasswordResetToken表，用details字段存储新邮箱）
            reset_token = PasswordResetToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                used=False
            )
            
            # 将新邮箱存储在token字段的前缀中（临时方案）
            # 格式：email_verify:{new_email}:{actual_token}
            reset_token.token = f"email_verify:{new_email}:{token}"
            
            session.add(reset_token)
            session.commit()
            
            return token
            
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()
    
    def send_email_verification(self, to_email: str, verification_link: str) -> bool:
        """
        发送邮箱验证邮件
        
        Args:
            to_email: 收件人邮箱
            verification_link: 验证链接
            
        Returns:
            bool: 是否发送成功
        """
        config = self.load_config()
        if not config:
            return False
        
        subject = "邮箱验证"
        
        # HTML 邮件内容
        html_content = f"""
        <html>
        <body>
            <h2>邮箱验证</h2>
            <p>您好！</p>
            <p>您请求将邮箱地址更改为：<strong>{to_email}</strong></p>
            <p>请点击下面的链接完成邮箱验证：</p>
            <p><a href="{verification_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">验证邮箱</a></p>
            <p>或者复制以下链接到浏览器地址栏：</p>
            <p><code>{verification_link}</code></p>
            <p><strong>注意：</strong></p>
            <ul>
                <li>此链接将在30分钟后失效</li>
                <li>如果您没有请求更改邮箱，请忽略此邮件</li>
                <li>验证完成后，您的邮箱地址将被更新</li>
            </ul>
            <p>如有疑问，请联系系统管理员。</p>
            <hr>
            <p><small>此邮件由系统自动发送，请勿回复。</small></p>
        </body>
        </html>
        """
        
        # 纯文本内容（备用）
        text_content = f"""
        邮箱验证
        
        您好！
        
        您请求将邮箱地址更改为：{to_email}
        
        请复制以下链接到浏览器地址栏完成邮箱验证：
        
        {verification_link}
        
        注意：
        - 此链接将在30分钟后失效
        - 如果您没有请求更改邮箱，请忽略此邮件
        - 验证完成后，您的邮箱地址将被更新
        
        如有疑问，请联系系统管理员。
        
        此邮件由系统自动发送，请勿回复。
        """
        
        success, message = self._send_email(to_email, subject, text_content, html_content, config)
        return success
    
    def verify_email_token(self, token: str) -> Dict[str, Any]:
        """
        验证邮箱验证令牌
        
        Args:
            token: 验证令牌
            
        Returns:
            Dict: 验证结果 {'success': bool, 'user_id': int, 'new_email': str, 'message': str}
        """
        session = get_session(self.db_url)
        try:
            # 查找令牌（需要匹配email_verify前缀）
            reset_token = session.query(PasswordResetToken).filter(
                PasswordResetToken.token.like(f"email_verify:%:{token}")
            ).first()
            
            if not reset_token:
                return {'success': False, 'message': '验证令牌无效'}
            
            # 检查是否已使用
            if reset_token.used:
                return {'success': False, 'message': '验证令牌已使用'}
            
            # 检查是否过期
            if datetime.now() > reset_token.expires_at:
                return {'success': False, 'message': '验证令牌已过期'}
            
            # 解析新邮箱地址
            token_parts = reset_token.token.split(':')
            if len(token_parts) != 3 or token_parts[0] != 'email_verify':
                return {'success': False, 'message': '验证令牌格式错误'}
            
            new_email = token_parts[1]
            
            # 标记令牌为已使用
            reset_token.used = True
            session.commit()
            
            return {
                'success': True,
                'user_id': reset_token.user_id,
                'new_email': new_email,
                'message': '邮箱验证成功'
            }
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': f'验证失败：{str(e)}'}
        finally:
            session.close()
    
    def _send_email(self, to_email: str, subject: str, text_content: str, 
                   html_content: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        发送邮件的内部方法
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            text_content: 纯文本内容
            html_content: HTML内容
            config: 邮件配置
            
        Returns:
            Tuple[bool, str]: (成功, 消息)
        """
        try:
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            
            # 正确格式化 From 头，遵循 RFC5322 标准
            from email.utils import formataddr, make_msgid
            sender_name = config.get('sender_name', '').strip()
            sender_email = config['sender_email'].strip()
            
            # 验证发件人邮箱格式
            if not sender_email or '@' not in sender_email:
                return False, "发件人邮箱地址格式无效"
            
            # 使用 formataddr 确保正确的 RFC5322 格式
            if sender_name:
                msg['From'] = formataddr((sender_name, sender_email))
            else:
                msg['From'] = sender_email
            
            msg['To'] = to_email
            
            # 添加 Date 头（RFC5322 要求）
            from email.utils import formatdate
            msg['Date'] = formatdate(localtime=True)
            
            # 添加 Message-ID 头（RFC5322 推荐）
            msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[1])
            
            # 添加纯文本和HTML内容
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # 创建SMTP连接
            if config.get('use_ssl', False):
                # 使用SSL
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(config['smtp_host'], config['smtp_port'], context=context)
            else:
                # 使用普通连接或TLS
                server = smtplib.SMTP(config['smtp_host'], config['smtp_port'])
                if config.get('use_tls', True):
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # 登录（如果需要）
            if config.get('smtp_username') and config.get('smtp_password'):
                server.login(config['smtp_username'], config['smtp_password'])
            
            # 发送邮件
            server.send_message(msg)
            server.quit()
            
            return True, "邮件发送成功"
            
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP认证失败，请检查用户名和密码"
        except smtplib.SMTPConnectError:
            return False, "无法连接到SMTP服务器，请检查服务器地址和端口"
        except smtplib.SMTPRecipientsRefused:
            return False, "收件人邮箱地址被拒绝"
        except smtplib.SMTPSenderRefused:
            return False, "发件人邮箱地址被拒绝"
        except Exception as e:
            return False, f"邮件发送失败：{str(e)}"
    
    def is_configured(self) -> bool:
        """
        检查邮件服务是否已配置
        
        Returns:
            bool: 是否已配置
        """
        config = self.load_config()
        if not config:
            return False
        
        # 检查必要的配置项
        required_fields = ['smtp_host', 'smtp_port', 'sender_email']
        return all(config.get(field) for field in required_fields)