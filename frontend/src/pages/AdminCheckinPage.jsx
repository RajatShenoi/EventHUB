import { Html5QrcodeScanner } from 'html5-qrcode';
import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';

export default function AdminCheckinPage() {
  const scannerRef = useRef(null);
  const scannerContainerRef = useRef(null);
  const scanLockRef = useRef(false);
  const [manualToken, setManualToken] = useState('');
  const [scanMessage, setScanMessage] = useState('');
  const [scanPopup, setScanPopup] = useState(null);
  const [history, setHistory] = useState([]);

  const stopScanner = async () => {
    const scanner = scannerRef.current;
    scannerRef.current = null;

    if (scanner) {
      try {
        await scanner.clear();
      } catch {
        if (scannerContainerRef.current) {
          scannerContainerRef.current.innerHTML = '';
        }
      }
    }

    if (scannerContainerRef.current) {
      scannerContainerRef.current.innerHTML = '';
    }
  };

  const startScanner = () => {
    if (scannerRef.current || !scannerContainerRef.current) {
      return;
    }

    scanLockRef.current = false;
    scannerContainerRef.current.innerHTML = '';

    const scanner = new Html5QrcodeScanner('qr-reader', { fps: 10, qrbox: 220 }, false);

    scanner.render(
      async (decodedText) => {
        if (scanLockRef.current) {
          return;
        }

        scanLockRef.current = true;
        await stopScanner();
        await submitScan(decodedText, true);
      },
      () => {}
    );

    scannerRef.current = scanner;
  };

  const refreshHistory = () => {
    api
      .get('/checkin/history')
      .then((res) => setHistory(res.data))
      .catch((err) => setScanMessage(err.message));
  };

  const submitScan = async (qr_token) => {
    if (!qr_token) {
      return;
    }
    try {
      const res = await api.post('/checkin/scan', { qr_token });
      const result = res.data.result;
      const registration = res.data.registration;
      const message =
        result === 'success'
          ? `${registration?.event_title || 'Registration'} checked in successfully.`
          : 'This user is already checked in.';

      setScanMessage(message);
      setScanPopup({
        title: result === 'success' ? 'Check-in successful' : 'Check-in already recorded',
        message,
        kind: result === 'success' ? 'success' : 'warning',
      });
      refreshHistory();
    } catch (err) {
      setScanMessage(err.message);
      setScanPopup({
        title: 'Check-in failed',
        message: err.message,
        kind: 'error',
      });
    }
  };

  useEffect(() => {
    refreshHistory();

    startScanner();

    return () => {
      stopScanner();
    };
  }, []);

  return (
    <div className="container">
      <h1>Admin Check-in Scanner</h1>
      <p>Scan participant QR from camera or paste token manually.</p>
      <div id="qr-reader" ref={scannerContainerRef} className="card" />

      <section className="card">
        <h3>Manual Check-in</h3>
        <textarea
          rows="4"
          placeholder="Paste QR token"
          value={manualToken}
          onChange={(e) => setManualToken(e.target.value)}
        />
        <button className="button-primary" onClick={() => submitScan(manualToken)}>
          Submit Token
        </button>
      </section>

      {scanMessage && <p className="notice">{scanMessage}</p>}

      {scanPopup && (
        <div className="modal-backdrop" role="presentation" onClick={() => setScanPopup(null)}>
          <div className={`modal-card modal-${scanPopup.kind}`} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <h2>{scanPopup.title}</h2>
            <p>{scanPopup.message}</p>
            <div className="stack-horizontal">
              <button
                className="button-primary"
                onClick={async () => {
                  setScanPopup(null);
                  await stopScanner();
                  startScanner();
                }}
              >
                Scan Next QR
              </button>
              <button
                className="button-secondary"
                onClick={async () => {
                  setScanPopup(null);
                  await stopScanner();
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <section className="card">
        <h2>Recent Scan History</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Registration</th>
              <th>Result</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item) => (
              <tr key={item.id}>
                <td>{new Date(item.scanned_at).toLocaleString()}</td>
                <td>{item.registration_id}</td>
                <td>{item.result}</td>
                <td>{item.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
