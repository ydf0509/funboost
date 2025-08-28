# funboost/consumers/cdc_consumer.py

import time
import typing
from funboost.consumers.base_consumer import AbstractConsumer
from funboost.core.loggers import develop_logger

# pip install mysql-replication==1.0.9
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    DeleteRowsEvent,
    UpdateRowsEvent,
    WriteRowsEvent,
)



class MysqlCdcConsumer(AbstractConsumer):
    """
    A consumer that listens to MySQL binlog events (CDC) and treats them as tasks.
    This broker is consumer-driven; it automatically generates tasks from database changes.
    """

    BROKER_EXCLUSIVE_CONFIG_DEFAULT = {
        'BinLogStreamReaderConfig': {},
    }

    def custom_init(self):
        """Validates the essential configuration."""
        config = self.consumer_params.broker_exclusive_config['BinLogStreamReaderConfig']
        if not config.get('connection_settings') or not config.get('server_id'):
            raise ValueError("For 'funboost_cdc' broker, 'connection_settings' and 'server_id' must be provided in 'broker_exclusive_config'.")
        self.logger.info("FunboostCdcConsumer initialized. Ready to listen for binlog events.")
        self._bin_log_stream_reader_config = config

    def _shedual_task(self):
        """
        This is the main loop that connects to MySQL, reads binlog events,
        and submits them as tasks to the funboost engine.
        """
        # Prepare the arguments for BinLogStreamReader by filtering out None values


        stream = BinLogStreamReader(**self._bin_log_stream_reader_config)

        try:
            for binlogevent in stream:
                event_type = None
                if isinstance(binlogevent, WriteRowsEvent):
                    event_type = 'INSERT'
                elif isinstance(binlogevent, UpdateRowsEvent):
                    event_type = 'UPDATE'
                elif isinstance(binlogevent, DeleteRowsEvent):
                    event_type = 'DELETE'

                if event_type:
                    for row in binlogevent.rows:
                        # Construct a clear, flat dictionary to be used as function kwargs
                        task_body = {
                            'event_type': event_type,
                            'schema': binlogevent.schema,
                            'table': binlogevent.table,
                            'timestamp': binlogevent.timestamp,
                        }
                        # Unpack row data ('values' or 'before_values'/'after_values')
                        task_body.update(row)

                        # Submit the structured data as a task to the funboost engine
                        self._submit_task({'body': task_body})
        except Exception as e:
            self.logger.critical(f"An error occurred in the binlog stream: {e}", exc_info=True)
            # A small delay before potentially restarting or exiting, depending on supervisor.
            time.sleep(10)
        finally:
            self.logger.info("Closing binlog stream.")
            stream.close()

    def _confirm_consume(self, kw: dict):
        """
        Confirmation is implicitly handled by the BinLogStreamReader's position management.
        When resume_stream=True, the library automatically saves its position.
        Funboost's ACK here confirms that the *processing* of the event is complete.
        """
        pass

    def _requeue(self, kw: dict):
        """
        Requeuing a binlog event is not a standard operation.
        Funboost's built-in retry mechanism should be used for transient processing errors.
        If a task fails permanently, it will be ACK'd after exhausting retries,
        and the binlog position will eventually advance.
        """
        self.logger.warning(f"Requeuing a CDC event is not supported. "
                            f"Use funboost's retry mechanism for processing failures. Task: {kw.get('body')}")
        pass