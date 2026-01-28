/**
 * 前端密码加密模块
 *
 * 使用 RSA-OAEP 加密密码，提供额外的传输安全层。
 * 在 HTTPS 之上提供防护，防止密码在日志、中间代理等场景下被明文暴露。
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

/** 公钥响应格式 */
export interface PublicKeyResponse {
  public_key: string;
  key_id: string;
}

/** 加密密码格式 */
export interface EncryptedPassword {
  encrypted: true;
  data: string; // Base64 encoded
  key_id: string;
}

/** 缓存的公钥 */
let cachedPublicKey: PublicKeyResponse | null = null;
let cacheTimestamp: number = 0;
const CACHE_DURATION_MS = 30 * 60 * 1000; // 30 分钟缓存

/**
 * 获取服务器公钥
 *
 * @returns 公钥和密钥ID
 * @throws Error 如果获取失败
 */
export async function fetchPublicKey(): Promise<PublicKeyResponse> {
  // 检查缓存
  const now = Date.now();
  if (cachedPublicKey && now - cacheTimestamp < CACHE_DURATION_MS) {
    return cachedPublicKey;
  }

  try {
    const response = await fetch(`${API_BASE}/api/public_key`, {
      method: "GET",
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(`获取公钥失败: ${response.status}`);
    }

    const data: PublicKeyResponse = await response.json();

    if (!data.public_key || !data.key_id) {
      throw new Error("公钥响应格式无效");
    }

    // 更新缓存
    cachedPublicKey = data;
    cacheTimestamp = now;

    return data;
  } catch (error) {
    // 清除缓存
    cachedPublicKey = null;
    cacheTimestamp = 0;
    throw error;
  }
}

/**
 * 清除公钥缓存
 */
export function clearPublicKeyCache(): void {
  cachedPublicKey = null;
  cacheTimestamp = 0;
}


/**
 * 将 PEM 格式公钥转换为 CryptoKey
 *
 * @param pemKey PEM 格式的公钥
 * @returns CryptoKey 对象
 */
async function importPublicKey(pemKey: string): Promise<CryptoKey> {
  // 移除 PEM 头尾和换行符
  const pemHeader = "-----BEGIN PUBLIC KEY-----";
  const pemFooter = "-----END PUBLIC KEY-----";

  let pemContents = pemKey.replace(pemHeader, "").replace(pemFooter, "");
  pemContents = pemContents.replace(/\s/g, "");

  // Base64 解码
  const binaryDer = Uint8Array.from(atob(pemContents), (c) => c.charCodeAt(0));

  // 导入公钥
  return await crypto.subtle.importKey(
    "spki",
    binaryDer,
    {
      name: "RSA-OAEP",
      hash: "SHA-256",
    },
    false,
    ["encrypt"]
  );
}

/**
 * 使用公钥加密密码
 *
 * @param password 明文密码
 * @param publicKeyPem PEM 格式公钥
 * @returns Base64 编码的加密数据
 */
export async function encryptPassword(password: string, publicKeyPem: string): Promise<string> {
  // 导入公钥
  const publicKey = await importPublicKey(publicKeyPem);

  // 将密码转换为 Uint8Array
  const encoder = new TextEncoder();
  const passwordBytes = encoder.encode(password);

  // 使用 RSA-OAEP 加密
  const encryptedBuffer = await crypto.subtle.encrypt(
    {
      name: "RSA-OAEP",
    },
    publicKey,
    passwordBytes
  );

  // 转换为 Base64
  const encryptedArray = new Uint8Array(encryptedBuffer);
  let binary = "";
  for (let i = 0; i < encryptedArray.length; i++) {
    binary += String.fromCharCode(encryptedArray[i]);
  }
  return btoa(binary);
}

/**
 * 检查是否支持 Web Crypto API
 */
export function isEncryptionSupported(): boolean {
  return (
    typeof crypto !== "undefined" &&
    typeof crypto.subtle !== "undefined" &&
    typeof crypto.subtle.encrypt === "function"
  );
}

/**
 * 准备加密的密码数据用于传输
 *
 * 如果加密可用，返回加密后的密码对象；
 * 如果加密不可用（如不支持 Web Crypto API），返回明文密码。
 *
 * @param password 明文密码
 * @returns 加密后的密码对象，或在加密不可用时返回明文
 */
export async function preparePassword(password: string): Promise<EncryptedPassword | string> {
  // 检查是否支持加密
  if (!isEncryptionSupported()) {
    console.warn("Web Crypto API 不可用，将使用明文密码");
    return password;
  }

  try {
    // 清除可能过期的缓存，确保获取最新公钥
    // 这样可以避免服务器重启后密钥不匹配的问题
    clearPublicKeyCache();
    
    // 获取公钥
    const keyData = await fetchPublicKey();

    // 加密密码
    const encryptedData = await encryptPassword(password, keyData.public_key);

    // 返回加密格式
    return {
      encrypted: true,
      data: encryptedData,
      key_id: keyData.key_id,
    };
  } catch (error) {
    console.error("密码加密失败:", error);
    throw new Error("密码加密失败，请刷新页面重试");
  }
}

/**
 * 准备多个密码用于传输（如改密码场景）
 *
 * @param passwords 密码对象，键为字段名，值为明文密码
 * @returns 加密后的密码对象
 */
export async function preparePasswords<T extends Record<string, string>>(
  passwords: T
): Promise<Record<keyof T, EncryptedPassword | string>> {
  // 检查是否支持加密
  if (!isEncryptionSupported()) {
    console.warn("Web Crypto API 不可用，将使用明文密码");
    return passwords as Record<keyof T, EncryptedPassword | string>;
  }

  try {
    // 清除可能过期的缓存，确保获取最新公钥
    clearPublicKeyCache();
    
    // 获取公钥（只获取一次）
    const keyData = await fetchPublicKey();

    // 加密所有密码
    const result: Record<string, EncryptedPassword | string> = {};

    for (const [key, value] of Object.entries(passwords)) {
      const encryptedData = await encryptPassword(value, keyData.public_key);
      result[key] = {
        encrypted: true,
        data: encryptedData,
        key_id: keyData.key_id,
      };
    }

    return result as Record<keyof T, EncryptedPassword | string>;
  } catch (error) {
    console.error("密码加密失败:", error);
    throw new Error("密码加密失败，请刷新页面重试");
  }
}
