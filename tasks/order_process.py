import time

from funboost import (
    BoosterParams,
    BrokerEnum,
    boost,
    fct,
    FunctionResultStatusPersistanceConfig,
)

from sdk import KingdeeClient, HupunClient, get_current_env


class OrderProjectParams(BoosterParams):
    """订单项目配置类 - 封装公共参数"""

    project_name: str = "order_process"
    broker_kind: BrokerEnum = BrokerEnum.REDIS_STREAM
    is_auto_start_consuming_message: bool = True
    is_using_rpc_mode: bool = True
    is_send_consumer_heartbeat_to_redis: bool = True
    function_result_status_persistance_conf: FunctionResultStatusPersistanceConfig = (
        FunctionResultStatusPersistanceConfig(
            is_save_result=True,
            is_save_status=True,
            expire_seconds=7 * 24 * 3600,
            is_use_bulk_insert=True,  # 批量插入，每 0.5 秒写入一次，性能更好
        )
    )


@boost(
    OrderProjectParams(
        queue_name="q_order_handler",  # 可用中文名方便看
        user_options={
            "handles": {
                "doc_type": "PUR_PurchaseOrder",
                "operation_type": "unaudit",  # 反审核操作
            }
        },
    )
)
def handle_order(doc_id: str, doc_type: str, operation_type: str, content: dict):
    fct.logger.info(
        f"[order] handling doc_id={doc_id}, type={doc_type}, op={operation_type}"
    )

    try:
        # 尝试获取 KingdeeClient 实例
        kingdee_client = KingdeeClient.get_instance()
    except ImportError as e:
        # 如果缺少 K3Cloud SDK，记录错误并返回失败状态
        fct.logger.error(f"K3Cloud SDK not available: {e}")
        return {
            "success": False,
            "error": "K3Cloud SDK not installed",
            "message": str(e),
            "doc_id": doc_id,
            "doc_type": doc_type,
            "operation_type": operation_type
        }

    # 1. 定义业务对象标识
    form_id = doc_type

    # 2. 定义数据体
    data = {
        "Number": doc_id,  # 单据号
        # "Id": "",               # 内码ID（可留空）
        # "CreateOrgId": 0        # 可选
    }

    try:
        response = kingdee_client.View(form_id, data)
        print(response)
        return response
    except Exception as e:
        fct.logger.error(f"Failed to process order {doc_id}: {e}")
        return {
            "success": False,
            "error": "Failed to process order",
            "message": str(e),
            "doc_id": doc_id,
            "doc_type": doc_type,
            "operation_type": operation_type
        }
