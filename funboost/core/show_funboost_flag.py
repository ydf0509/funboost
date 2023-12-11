
from funboost.core.loggers import flogger

funboost_flag_str = '''

                                                                                                                                                                                                          
FFFFFFFFFFFFFFFFFFFFFF     UUUUUUUU     UUUUUUUU     NNNNNNNN        NNNNNNNN     BBBBBBBBBBBBBBBBB             OOOOOOOOO               OOOOOOOOO             SSSSSSSSSSSSSSS      TTTTTTTTTTTTTTTTTTTTTTT
F::::::::::::::::::::F     U::::::U     U::::::U     N:::::::N       N::::::N     B::::::::::::::::B          OO:::::::::OO           OO:::::::::OO         SS:::::::::::::::S     T:::::::::::::::::::::T
F::::::::::::::::::::F     U::::::U     U::::::U     N::::::::N      N::::::N     B::::::BBBBBB:::::B       OO:::::::::::::OO       OO:::::::::::::OO      S:::::SSSSSS::::::S     T:::::::::::::::::::::T
FF::::::FFFFFFFFF::::F     UU:::::U     U:::::UU     N:::::::::N     N::::::N     BB:::::B     B:::::B     O:::::::OOO:::::::O     O:::::::OOO:::::::O     S:::::S     SSSSSSS     T:::::TT:::::::TT:::::T
  F:::::F       FFFFFF      U:::::U     U:::::U      N::::::::::N    N::::::N       B::::B     B:::::B     O::::::O   O::::::O     O::::::O   O::::::O     S:::::S                 TTTTTT  T:::::T  TTTTTT
  F:::::F                   U:::::D     D:::::U      N:::::::::::N   N::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O     S:::::S                         T:::::T        
  F::::::FFFFFFFFFF         U:::::D     D:::::U      N:::::::N::::N  N::::::N       B::::BBBBBB:::::B      O:::::O     O:::::O     O:::::O     O:::::O      S::::SSSS                      T:::::T        
  F:::::::::::::::F         U:::::D     D:::::U      N::::::N N::::N N::::::N       B:::::::::::::BB       O:::::O     O:::::O     O:::::O     O:::::O       SS::::::SSSSS                 T:::::T        
  F:::::::::::::::F         U:::::D     D:::::U      N::::::N  N::::N:::::::N       B::::BBBBBB:::::B      O:::::O     O:::::O     O:::::O     O:::::O         SSS::::::::SS               T:::::T        
  F::::::FFFFFFFFFF         U:::::D     D:::::U      N::::::N   N:::::::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O            SSSSSS::::S              T:::::T        
  F:::::F                   U:::::D     D:::::U      N::::::N    N::::::::::N       B::::B     B:::::B     O:::::O     O:::::O     O:::::O     O:::::O                 S:::::S             T:::::T        
  F:::::F                   U::::::U   U::::::U      N::::::N     N:::::::::N       B::::B     B:::::B     O::::::O   O::::::O     O::::::O   O::::::O                 S:::::S             T:::::T        
FF:::::::FF                 U:::::::UUU:::::::U      N::::::N      N::::::::N     BB:::::BBBBBB::::::B     O:::::::OOO:::::::O     O:::::::OOO:::::::O     SSSSSSS     S:::::S           TT:::::::TT      
F::::::::FF                  UU:::::::::::::UU       N::::::N       N:::::::N     B:::::::::::::::::B       OO:::::::::::::OO       OO:::::::::::::OO      S::::::SSSSSS:::::S           T:::::::::T      
F::::::::FF                    UU:::::::::UU         N::::::N        N::::::N     B::::::::::::::::B          OO:::::::::OO           OO:::::::::OO        S:::::::::::::::SS            T:::::::::T      
FFFFFFFFFFF                      UUUUUUUUU           NNNNNNNN         NNNNNNN     BBBBBBBBBBBBBBBBB             OOOOOOOOO               OOOOOOOOO           SSSSSSSSSSSSSSS              TTTTTTTTTTT      
   

'''

funboost_flag_str2 = r'''

      ___                  ___                    ___                                           ___                    ___                    ___                          
     /  /\                /__/\                  /__/\                  _____                  /  /\                  /  /\                  /  /\                   ___   
    /  /:/_               \  \:\                 \  \:\                /  /::\                /  /::\                /  /::\                /  /:/_                 /  /\  
   /  /:/ /\               \  \:\                 \  \:\              /  /:/\:\              /  /:/\:\              /  /:/\:\              /  /:/ /\               /  /:/  
  /  /:/ /:/           ___  \  \:\            _____\__\:\            /  /:/~/::\            /  /:/  \:\            /  /:/  \:\            /  /:/ /::\             /  /:/   
 /__/:/ /:/           /__/\  \__\:\          /__/::::::::\          /__/:/ /:/\:|          /__/:/ \__\:\          /__/:/ \__\:\          /__/:/ /:/\:\           /  /::\   
 \  \:\/:/            \  \:\ /  /:/          \  \:\~~\~~\/          \  \:\/:/~/:/          \  \:\ /  /:/          \  \:\ /  /:/          \  \:\/:/~/:/          /__/:/\:\  
  \  \::/              \  \:\  /:/            \  \:\  ~~~            \  \::/ /:/            \  \:\  /:/            \  \:\  /:/            \  \::/ /:/           \__\/  \:\ 
   \  \:\               \  \:\/:/              \  \:\                 \  \:\/:/              \  \:\/:/              \  \:\/:/              \__\/ /:/                 \  \:\
    \  \:\               \  \::/                \  \:\                 \  \::/                \  \::/                \  \::/                 /__/:/                   \__\/
     \__\/                \__\/                  \__\/                  \__\/                  \__\/                  \__\/                  \__\/                         



'''

flogger.debug('\033[0m' + funboost_flag_str2 + '\033[0m')

flogger.info(f'''分布式函数调度框架funboost文档地址：  \033[0m https://funboost.readthedocs.io/zh/latest/ \033[0m ''')
