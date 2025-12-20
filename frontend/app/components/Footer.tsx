import Image from "next/image";
import styles from "./Components.module.css";
import madr_logo_site from "@images/madr-logo-site.svg";
import whatsapp from "@images/whatsapp-sem-fundo.png";
import instagram from "@images/instagram-sem-fundo.png";
import facebook from "@images/facebook-sem-fundo.png";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <section className={styles.divLogoFooter}>
        <article className={styles.divLogo}>
          <Image src={madr_logo_site} className={styles.madrLogoSite1Icon} width={112} height={54} sizes="100vw" alt="" />
          <p className="p-white">Meu arquivo digital de romances</p>
        </article>
        <article className={styles.divRedeSocial}>
          <Image src={facebook} className={styles.facebookSemFundo1Icon} width={46} height={49} sizes="100vw" alt="" />
          <Image src={instagram} className={styles.instagramSemFundo1Icon} width={47} height={45} sizes="100vw" alt="" />
          <Image src={whatsapp} className={styles.instagramSemFundo1Icon} width={47} height={44} sizes="100vw" alt="" />
        </article>
      </section>
      <p className="p-white">© Copyrights - Todos os direitos reservados. | Empresa fictícia Madr. Criada para trabalho educacional.</p>
    </footer>
  );
}
