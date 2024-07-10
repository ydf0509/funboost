from funboost import EmptyConsumer


class FastStreamConsumer(EmptyConsumer):
    def custom_init(self):
        pass


    def _shedual_task(self):
        raise NotImplemented('not realization')


    def _confirm_consume(self, kw):
        raise NotImplemented('not realization')


    def _requeue(self, kw):
        raise NotImplemented('not realization')