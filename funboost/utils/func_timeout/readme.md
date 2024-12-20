

# 基于三方包func_timeout的改动点


主要是把  StoppableThread 和 JoinThread 改成了继承 FctContextThread 而非 threading.Thread


原因是为了支持把当前线程的 funboost上下文传给 超时的单独的线程中， 方便用设置了超时后还能用 funboost上下文 funboost_current_task