"use client";

import { useEffect, useState } from "react";
import { AlertCircle, RefreshCw, Save, X } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { TextArea } from "@/components/ui/TextArea";
import { apiFetch } from "@/lib/api";

// ============================================================================
// Types
// ============================================================================

export type ProjectFormData = {
  id?: number;
  name: string;
  code: string;
  description: string;
  status: string;
};

type ProjectDialogProps = {
  open: boolean;
  onClose: () => void;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
  /** 编辑模式时传入项目数据，创建模式时为 null */
  project: ProjectFormData | null;
};

type FormErrors = {
  name?: string;
  code?: string;
  description?: string;
};

// ============================================================================
// Constants
// ============================================================================

const INITIAL_FORM: ProjectFormData = {
  name: "",
  code: "",
  description: "",
  status: "active",
};

/** 项目代码正则：小写字母开头，只能包含小写字母、数字、下划线 */
const CODE_PATTERN = /^[a-z][a-z0-9_]*$/;

// ============================================================================
// Component
// ============================================================================

export function ProjectDialog({
  open,
  onClose,
  onSuccess,
  onError,
  project,
}: ProjectDialogProps) {
  const isEditMode = !!project?.id;
  
  // 表单状态
  const [form, setForm] = useState<ProjectFormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // 当 project 变化时重置表单
  useEffect(() => {
    if (open) {
      if (project) {
        setForm({
          id: project.id,
          name: project.name || "",
          code: project.code || "",
          description: project.description || "",
          status: project.status || "active",
        });
      } else {
        setForm(INITIAL_FORM);
      }
      setErrors({});
      setTouched({});
    }
  }, [open, project]);

  // 表单验证
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // 项目名称验证
    if (!form.name.trim()) {
      newErrors.name = "项目名称不能为空";
    } else if (form.name.length > 64) {
      newErrors.name = "项目名称不能超过 64 个字符";
    }

    // 项目代码验证
    if (!form.code.trim()) {
      newErrors.code = "项目代码不能为空";
    } else if (form.code.length > 32) {
      newErrors.code = "项目代码不能超过 32 个字符";
    } else if (!CODE_PATTERN.test(form.code)) {
      newErrors.code = "项目代码必须以小写字母开头，只能包含小写字母、数字和下划线";
    }

    // 描述验证
    if (form.description && form.description.length > 256) {
      newErrors.description = "项目描述不能超过 256 个字符";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 字段变化处理
  const handleFieldChange = (field: keyof ProjectFormData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    
    // 清除该字段的错误
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  // 字段失焦处理
  const handleFieldBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    validateForm();
  };

  // 提交表单
  const handleSubmit = async () => {
    // 标记所有字段为已触摸
    setTouched({ name: true, code: true, description: true });
    
    if (!validateForm()) {
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        code: form.code.trim(),
        description: form.description.trim(),
        status: form.status,
      };

      if (isEditMode) {
        // 更新项目
        const response = await apiFetch<{ success: boolean; error?: string }>(
          `/admin/api/projects/${form.id}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }
        );
        if (!response.success) {
          throw new Error(response.error || "更新项目失败");
        }
        onSuccess(`项目 "${form.name}" 更新成功`);
      } else {
        // 创建项目
        const response = await apiFetch<{ success: boolean; error?: string }>(
          `/admin/api/projects`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }
        );
        if (!response.success) {
          throw new Error(response.error || "创建项目失败");
        }
        onSuccess(`项目 "${form.name}" 创建成功`);
      }
      onClose();
    } catch (err) {
      onError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setSaving(false);
    }
  };

  // 关闭对话框
  const handleClose = () => {
    if (!saving) {
      onClose();
    }
  };

  return (
    <Modal
      open={open}
      title={isEditMode ? `编辑项目: ${project?.name}` : "创建项目"}
      onClose={handleClose}
      size="md"
      footer={
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleClose}
            disabled={saving}
            className="cursor-pointer"
          >
            <X className="h-4 w-4" />
            取消
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            disabled={saving}
            className="cursor-pointer"
          >
            {saving ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                {isEditMode ? "保存修改" : "创建项目"}
              </>
            )}
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        {/* 项目名称 */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            项目名称 <span className="text-[hsl(var(--danger))]">*</span>
          </label>
          <Input
            value={form.name}
            onChange={(e) => handleFieldChange("name", e.target.value)}
            onBlur={() => handleFieldBlur("name")}
            placeholder="输入项目名称，如：订单系统"
            maxLength={64}
            className={touched.name && errors.name ? "border-[hsl(var(--danger))]" : ""}
          />
          {touched.name && errors.name && (
            <p className="flex items-center gap-1 text-xs text-[hsl(var(--danger))]">
              <AlertCircle className="h-3 w-3" />
              {errors.name}
            </p>
          )}
          <p className="text-xs text-[hsl(var(--ink-muted))]">
            {form.name.length}/64 字符
          </p>
        </div>

        {/* 项目代码 */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            项目代码 <span className="text-[hsl(var(--danger))]">*</span>
          </label>
          <Input
            value={form.code}
            onChange={(e) => handleFieldChange("code", e.target.value.toLowerCase())}
            onBlur={() => handleFieldBlur("code")}
            placeholder="输入项目代码，如：order_system"
            maxLength={32}
            disabled={isEditMode}
            className={touched.code && errors.code ? "border-[hsl(var(--danger))]" : ""}
          />
          {touched.code && errors.code && (
            <p className="flex items-center gap-1 text-xs text-[hsl(var(--danger))]">
              <AlertCircle className="h-3 w-3" />
              {errors.code}
            </p>
          )}
          {isEditMode ? (
            <p className="flex items-center gap-1 text-xs text-[hsl(var(--warning))]">
              <AlertCircle className="h-3 w-3" />
              项目代码创建后不可修改，因为它用于权限标识
            </p>
          ) : (
            <p className="text-xs text-[hsl(var(--ink-muted))]">
              {form.code.length}/32 字符 · 小写字母开头，只能包含小写字母、数字和下划线
            </p>
          )}
        </div>

        {/* 项目描述 */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            项目描述
          </label>
          <TextArea
            value={form.description}
            onChange={(e) => handleFieldChange("description", e.target.value)}
            onBlur={() => handleFieldBlur("description")}
            placeholder="输入项目描述（可选）"
            maxLength={256}
            className={`min-h-[80px] ${touched.description && errors.description ? "border-[hsl(var(--danger))]" : ""}`}
          />
          {touched.description && errors.description && (
            <p className="flex items-center gap-1 text-xs text-[hsl(var(--danger))]">
              <AlertCircle className="h-3 w-3" />
              {errors.description}
            </p>
          )}
          <p className="text-xs text-[hsl(var(--ink-muted))]">
            {form.description.length}/256 字符
          </p>
        </div>

        {/* 项目状态 */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            项目状态
          </label>
          <Select
            value={form.status}
            onChange={(e) => handleFieldChange("status", e.target.value)}
          >
            <option value="active">启用</option>
            <option value="archived">已归档</option>
          </Select>
          <p className="text-xs text-[hsl(var(--ink-muted))]">
            已归档的项目将不会在项目选择器中显示
          </p>
        </div>
      </div>
    </Modal>
  );
}
