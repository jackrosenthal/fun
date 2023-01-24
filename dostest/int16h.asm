segment _TEXT public class=CODE
        global int16h_
        extern int16_c_

int16h_:
        push ebp
        mov ebp, esp

        push ecx
        push edx
        push ebx
        push esi
        push edi

        call int16_c_

        pop edi
        pop esi
        pop ebx
        pop edx
        pop ecx

        pop ebp

        iret
