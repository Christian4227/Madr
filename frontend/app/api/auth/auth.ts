"use server";

import { z } from "zod";
// import { signIn } from '@/auth'; // Descomente se estiver usando NextAuth/Auth.js
// import { redirect } from 'next/navigation';

// Definição do esquema de validação
const LoginSchema = z.object({
  email: z.string().email({ message: "Por favor, insira um e-mail válido." }),
  password: z.string().min(6, { message: "A senha deve ter pelo menos 6 caracteres." }),
});

// Tipo para o estado do formulário
export type LoginState = {
  errors?: {
    email?: string[];
    password?: string[];
  };
  message?: string | null;
};

export async function authenticate(prevState: LoginState | undefined, formData: FormData): Promise<LoginState> {
  // Validar os campos do formulário usando Zod
  const validatedFields = LoginSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });

  // Se a validação falhar, retornar os erros imediatamente
  if (!validatedFields.success) {
    return {
      errors: validatedFields.error.flatten().fieldErrors,
      message: "Campos inválidos. Falha ao realizar login.",
    };
  }

  const { email, password } = validatedFields.data;

  try {
    // Lógica de autenticação aqui. Exemplo com NextAuth:
    // await signIn('credentials', { email, password, redirect: false });

    console.log("Login solicitado para:", email);

    return { message: "Login realizado com sucesso!" };
  } catch (error) {
    return {
      message: "Erro de banco de dados: Falha ao realizar login.",
    };
  }
}
