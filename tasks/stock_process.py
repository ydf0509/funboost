from funboost import (
    BoosterParams,
    BrokerEnum,
    boost,
    fct,
    FunctionResultStatusPersistanceConfig,
)


class StockProjectParams(BoosterParams):
    """库存项目配置类 - 封装公共参数"""

    project_name: str = "stock_process"
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
    StockProjectParams(
        queue_name="q_stock_handler",
        user_options={
            "handles": {
                "doc_type": "stock",
                "operation_type": "*",  # 匹配所有操作类型
            }
        },
    )
)
def handle_stock(doc_id: str, doc_type: str, operation_type: str, content: dict):
    fct.logger.info(
        f"[stock] syncing doc_id={doc_id}, type={doc_type}, op={operation_type}"
    )
    return "stock_success"
