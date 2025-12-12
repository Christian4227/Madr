import Image from "next/image";
import styles from "./index.module.css";
import madr_hero from "@images/hero-madr-desktop-1.png";
import romance_romantico_1 from "@images/romance-romantico.png";
import icon_primeiro_lugar_1 from "@images/primeiro-lugar.svg";
import icon_autores_1 from "@images/icon-autores.svg";
import HeaderHome from "./components/HeaderHome";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <>
      <HeaderHome />
      <main>
        <section className={styles.hero}>
          <Image src={madr_hero} className={styles.heroMadrDesktop1Icon} width={635} height={635} sizes="100vw" alt="Madr Hero" />
          <article className={styles.divTitulo}>
            <h1 className={styles.madr}>Madr</h1>
            <h2 className={styles.meuArquivoDigital}>Meu arquivo digital de romances</h2>
          </article>
        </section>
        <section className={styles.apresentacao}>
          <h2>
            <b className={styles.madr}>
              Venha com a gente <br />e conte o seu romance!
            </b>
          </h2>
          <article className={styles.divCarrossel}>
            <div className={styles.divCard}>
              <Image src={romance_romantico_1} className={styles.romanceRomantico1Icon} width={420} height={234} sizes="100vw" alt="Romance" />
              <div className={styles.divCardSection}>
                <h3 className="h3-white">Romances online para ler</h3>
                <p className="p-white">Fique sempre por dentro do que acontece</p>
              </div>
            </div>
            <div className={styles.divCard}>
              <Image src={romance_romantico_1} className={styles.romanceRomantico1Icon} width={420} height={234} sizes="100vw" alt="Romance" />
              <div className={styles.divCardSection}>
                <h3 className="h3-white">Romances online para ler</h3>
                <p className="p-white">Fique sempre por dentro do que acontece</p>
              </div>
            </div>
            <div className={styles.divCard}>
              <Image src={romance_romantico_1} className={styles.romanceRomantico1Icon} width={420} height={234} sizes="100vw" alt="Romance" />
              <div className={styles.divCardSection}>
                <h3 className="h3-white">Romances online para ler</h3>
                <p className="p-white">Fique sempre por dentro do que acontece</p>
              </div>
            </div>
            <div className={styles.divCard}>
              <Image src={romance_romantico_1} className={styles.romanceRomantico1Icon} width={420} height={234} sizes="100vw" alt="Romance" />
              <div className={styles.divCardSection}>
                <h3 className="h3-white">Romances online para ler</h3>
                <p className="p-white">Fique sempre por dentro do que acontece</p>
              </div>
            </div>
            <div className={styles.divCard}>
              <Image src={romance_romantico_1} className={styles.romanceRomantico1Icon} width={420} height={234} sizes="100vw" alt="Romance" />
              <div className={styles.divCardSection}>
                <h3 className="h3-white">Romances online para ler</h3>
                <p className="p-white">Fique sempre por dentro do que acontece</p>
              </div>
            </div>
          </article>
        </section>
        <section className={styles.divServicos}>
          <article className={styles.divVantagens}>
            <div className={styles.divPremios}>
              <Image src={icon_primeiro_lugar_1} width={68} height={96} sizes="100vw" alt="Primeiro lugar" />
              <div className={styles.top1Parent}>
                <h3 className={styles.madr}>
                  <b>Top 1</b>
                </h3>
                <p className={styles.textoVantagem}>Sites de romances 2025</p>
              </div>
            </div>
            <div className={styles.divInfoCadastro}>
              <Image src={icon_autores_1} className={styles.iconAutores1} width={114} height={96} sizes="100vw" alt="Autores" />
              <div className={styles.diversosAutoresParent}>
                <h3 className={styles.vantagemTitulo}>Diversos autores</h3>
                <p className={styles.textoVantagem}>
                  Dom Casmurro, José de Alencar <br />e muito mais!{" "}
                </p>
              </div>
            </div>
            <div className={styles.divInfoCadastro}>
              <Image src={icon_autores_1} className={styles.iconAutores1} width={114} height={96} sizes="100vw" alt="Autores" />
              <div className={styles.diversosAutoresParent}>
                <h3 className={styles.vantagemTitulo}>Diversos autores</h3>
                <p className={styles.textoVantagem}>
                  Dom Casmurro, José de Alencar <br />e muito mais!{" "}
                </p>
              </div>
            </div>
            <div className={styles.divInfoCadastro}>
              <Image src={icon_autores_1} className={styles.iconAutores1} width={114} height={96} sizes="100vw" alt="Autores" />
              <div className={styles.diversosAutoresParent}>
                <h3 className={styles.vantagemTitulo}>Diversos autores</h3>
                <p className={styles.textoVantagem}>
                  Dom Casmurro, José de Alencar <br />e muito mais!{" "}
                </p>
              </div>
            </div>
            <div className={styles.divInfoCadastro}>
              <Image src={icon_autores_1} className={styles.iconAutores1} width={114} height={96} sizes="100vw" alt="Autores" />
              <div className={styles.diversosAutoresParent}>
                <h3 className={styles.vantagemTitulo}>Diversos autores</h3>
                <p className={styles.textoVantagem}>
                  Dom Casmurro, José de Alencar <br />e muito mais!{" "}
                </p>
              </div>
            </div>
            <div className={styles.divInfoCadastro}>
              <Image src={icon_autores_1} className={styles.iconAutores1} width={114} height={96} sizes="100vw" alt="Autores" />
              <div className={styles.diversosAutoresParent}>
                <h3 className={styles.vantagemTitulo}>Diversos autores</h3>
                <p className={styles.textoVantagem}>
                  Dom Casmurro, José de Alencar <br />e muito mais!{" "}
                </p>
              </div>
            </div>
          </article>
        </section>
        <div className={styles.divInfo} />
      </main>
      <Footer />
    </>
  );
}
