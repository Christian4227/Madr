"use server";

import { z } from "zod";
// import { signIn } from '@/auth'; // Descomente se estiver usando NextAuth/Auth.js
// import { redirect } from 'next/navigation';

// Definição do esquema de validação
const LoginSchema = z.object({
  username: z.string({ message: "Por favor, insira um e-mail válido." }),
  password: z.string().min(6, { message: "A senha deve ter pelo menos 6 caracteres." }),
});

export async function loginAuthentication(prevState: unknown, formData: FormData) {
  // Validar os campos do formulário usando Zod
  const validatedFields = LoginSchema.safeParse({
    usename: formData.get("username"),
    password: formData.get("password"),
  });

  // Se a validação falhar, retornar os erros imediatamente
  if (!validatedFields.success) {
    return {
      errors: z.treeifyError(validatedFields.error).properties,
      message: "Campos inválidos. Falha ao realizar login.",
      previousState: prevState,
    };
  }

  const { username, password } = validatedFields.data;

  try {
    // Lógica de autenticação aqui. Exemplo com NextAuth:
    // await signIn('credentials', { username, password, redirect: false });

    console.log("Login solicitado para:", username);

    return { message: "Login realizado com sucesso!" };
  } catch (error) {
    return {
      message: "Erro de banco de dados: Falha ao realizar login.",
    };
  }
}
