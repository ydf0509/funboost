import nb_log

logger = nb_log.get_logger('funboost.show_funboost_flag')

funboost_flag_str = '''
\033[0m
FFFFFFFFFFFFFFFFFFFFFFUUUUUUUU     UUUUUUUUNNNNNNNN        NNNNNNNNBBBBBBBBBBBBBBBBB        OOOOOOOOO          OOOOOOOOO        SSSSSSSSSSSSSSS TTTTTTTTTTTTTTTTTTTTTTT
F::::::::::::::::::::FU::::::U     U::::::UN:::::::N       N::::::NB::::::::::::::::B     OO:::::::::OO      OO:::::::::OO    SS:::::::::::::::ST:::::::::::::::::::::T
F::::::::::::::::::::FU::::::U     U::::::UN::::::::N      N::::::NB::::::BBBBBB:::::B  OO:::::::::::::OO  OO:::::::::::::OO S:::::SSSSSS::::::ST:::::::::::::::::::::T
FF::::::FFFFFFFFF::::FUU:::::U     U:::::UUN:::::::::N     N::::::NBB:::::B     B:::::BO:::::::OOO:::::::OO:::::::OOO:::::::OS:::::S     SSSSSSST:::::TT:::::::TT:::::T
  F:::::F       FFFFFF U:::::U     U:::::U N::::::::::N    N::::::N  B::::B     B:::::BO::::::O   O::::::OO::::::O   O::::::OS:::::S            TTTTTT  T:::::T  TTTTTT
  F:::::F              U:::::D     D:::::U N:::::::::::N   N::::::N  B::::B     B:::::BO:::::O     O:::::OO:::::O     O:::::OS:::::S                    T:::::T        
  F::::::FFFFFFFFFF    U:::::D     D:::::U N:::::::N::::N  N::::::N  B::::BBBBBB:::::B O:::::O     O:::::OO:::::O     O:::::O S::::SSSS                 T:::::T        
  F:::::::::::::::F    U:::::D     D:::::U N::::::N N::::N N::::::N  B:::::::::::::BB  O:::::O     O:::::OO:::::O     O:::::O  SS::::::SSSSS            T:::::T        
  F:::::::::::::::F    U:::::D     D:::::U N::::::N  N::::N:::::::N  B::::BBBBBB:::::B O:::::O     O:::::OO:::::O     O:::::O    SSS::::::::SS          T:::::T        
  F::::::FFFFFFFFFF    U:::::D     D:::::U N::::::N   N:::::::::::N  B::::B     B:::::BO:::::O     O:::::OO:::::O     O:::::O       SSSSSS::::S         T:::::T        
  F:::::F              U:::::D     D:::::U N::::::N    N::::::::::N  B::::B     B:::::BO:::::O     O:::::OO:::::O     O:::::O            S:::::S        T:::::T        
  F:::::F              U::::::U   U::::::U N::::::N     N:::::::::N  B::::B     B:::::BO::::::O   O::::::OO::::::O   O::::::O            S:::::S        T:::::T        
FF:::::::FF            U:::::::UUU:::::::U N::::::N      N::::::::NBB:::::BBBBBB::::::BO:::::::OOO:::::::OO:::::::OOO:::::::OSSSSSSS     S:::::S      TT:::::::TT      
F::::::::FF             UU:::::::::::::UU  N::::::N       N:::::::NB:::::::::::::::::B  OO:::::::::::::OO  OO:::::::::::::OO S::::::SSSSSS:::::S      T:::::::::T      
F::::::::FF               UU:::::::::UU    N::::::N        N::::::NB::::::::::::::::B     OO:::::::::OO      OO:::::::::OO   S:::::::::::::::SS       T:::::::::T      
FFFFFFFFFFF                 UUUUUUUUU      NNNNNNNN         NNNNNNNBBBBBBBBBBBBBBBBB        OOOOOOOOO          OOOOOOOOO      SSSSSSSSSSSSSSS         TTTTTTTTTTT 
\033[0m
'''

logger.debug(funboost_flag_str)

logger.info(f'''分布式函数调度框架文档地址：  \033[0m https://funboost.readthedocs.io/zh/latest/ \033[0m ''')