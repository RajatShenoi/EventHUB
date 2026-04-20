import { Html5QrcodeScanner } from 'html5-qrcode';
import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';

export default function AdminCheckinPage() {
  const scannerRef = useRef(null);
  const scannerContainerRef = useRef(null);
  const [manualToken, setManualToken] = useState('');
  const [scanMessage, setScanMessage] = useState('');
  const [history, setHistory] = useState([]);

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
      setScanMessage(`Scan result: ${res.data.result}`);
      refreshHistory();
    } catch (err) {
      setScanMessage(err.message);
    }
  };

  useEffect(() => {
    refreshHistory();

    if (scannerRef.current) {
      return undefined;
    }

    if (!scannerContainerRef.current) {
      return undefined;
    }

    scannerContainerRef.current.innerHTML = '';

    const scanner = new Html5QrcodeScanner('qr-reader', { fps: 10, qrbox: 220 }, false);

    scanner.render(
      (decodedText) => {
        submitScan(decodedText);
      },
      () => {}
    );

    scannerRef.current = scanner;

    return () => {
      if (scannerRef.current) {
        scannerRef.current.clear().catch(() => {
          if (scannerContainerRef.current) {
            scannerContainerRef.current.innerHTML = '';
          }
        });
        scannerRef.current = null;
      }
      if (scannerContainerRef.current) {
        scannerContainerRef.current.innerHTML = '';
      }
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
