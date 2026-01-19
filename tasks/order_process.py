import time

from funboost import (
    BoosterParams,
    BrokerEnum,
    boost,
    fct,
    FunctionResultStatusPersistanceConfig,
)



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

    return {"doc_id": doc_id, "status": "success", "message": f"Handled {doc_type} with operation {operation_type}"}