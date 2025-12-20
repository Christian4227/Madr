"use client";

import Image from "next/image";
import lupa from "@images/lupa-preto-1.svg";
import styles from "./Components.module.css";
import madr_logo_site from "@images/madr-logo-site.svg";
import { ModalLogin } from "./ui/ModalLogin";
import { useState } from "react";

export default function HeaderHome() {
  const [isOpen, setIsOpen] = useState(false);

  const toggleModal = () => {
    setIsOpen(!isOpen);
  };
  return (
    <>
      <header className={styles.header}>
        <Image src={madr_logo_site} width={112} height={54} sizes="100vw" alt="Pesquisar" />
        <div className={styles.divInputSearch}>
          <input type="search" name="TxtPesquisar" id="TxtPesquisar" className={styles.pesquisar} placeholder="Pesquisar" />
          <Image src={lupa} className={styles.lupaPreto1Icon} width={21} height={20} sizes="100vw" alt="Pesquisar" />
        </div>
        <div>
          <nav className={styles.divMenu}>
            <span className="span-white">Cadastre-se</span>
            <span className="span-white">|</span>
            <button onClick={() => toggleModal()}>
              <span className="span-white">Entrar</span>
            </button>
          </nav>
        </div>
      </header>
      <ModalLogin isOpen={isOpen} setIsOpen={setIsOpen} />
    </>
  );
}
