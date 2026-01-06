"use client";

import { Dialog, DialogPanel } from "@headlessui/react";
import styles from "../Components.module.css";
import { useActionState } from "react";
import { loginAuthentication } from "@/app/api/auth/login";

interface ModalLoginProps {
  isOpen: boolean;
  setIsOpen: (newMenuState: boolean) => void;
}

export function ModalLogin({ isOpen, setIsOpen }: ModalLoginProps) {
  const [state, formAction, isPending] = useActionState(loginAuthentication, null);

  return (
    <>
      <Dialog open={isOpen ?? false} onClose={() => setIsOpen(false)}>
        <div className="fixed inset-0 flex w-screen items-center justify-center bg-black/30 p-4">
          <DialogPanel className="w-[364px] px-6 py-12 bg-[var(--cor-fundo)] border border-[var(--cor-principal)] rounded-[10px] inline-flex flex-col justify-center items-center gap-8">
            <div className="text-center justify-start w-full">
              <span className="text-[var(--cor-principal)] text-2xl font-semibold font-['Inter']">
                Bem-vindo à <br />
              </span>
              <span className="text-[var(--cor-principal)] text-3xl font-bold font-['Calisto_MT']">Madr</span>
            </div>

            <form action={formAction} onSubmit={(e) => e.preventDefault()} className="flex flex-col gap-4 w-full">
              <div className="w-full flex flex-col gap-2 self-strech">
                <div className="flex flex-col gap-1">
                  <label htmlFor="email">Usuário/E-mail</label>
                  <input type="text" name="email" id="email" placeholder="Nome do usuário/e-mail" maxLength={255} />
                  {state?.errors?.username && <p className="p-error">{state.errors.username.errors[0]}</p>}
                </div>

                <div className="flex flex-col gap-2 self-strech">
                  <label htmlFor="senha">Senha</label>
                  <input type="password" name="senha" id="senha" placeholder="Senha" minLength={8} />
                  {state?.errors?.password && <p className="p-error">{state.errors.password.errors[0]}</p>}
                </div>
              </div>

              <div className="w-full flex flex-col items-center gap-6 self-strech">
                <input type="submit" value="Entrar" className="button-primary button-form-submit" disabled={isPending} />

                <div className="w-full inline-flex gap-2">
                  <span className="span-primary">Não tem uma conta?</span>
                  <span className="span-primary underline">Cadastre-se</span>
                </div>
              </div>
            </form>
          </DialogPanel>
        </div>
      </Dialog>
    </>
  );
}
