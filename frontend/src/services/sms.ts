export interface SMSAlertPayload {
  groups: string[]
  message: string
  camera_name: string
  criticality: string
  lat?: number
  lon?: number
}

export async function sendSMSAlert(payload: SMSAlertPayload): Promise<{ sent: number }> {
  await new Promise(r => setTimeout(r, 800 + Math.random() * 700))

  console.log(
    `[SMS DEMO] Alert sent to ${payload.groups.length} group(s):\n` +
    `  Groups: ${payload.groups.join(', ')}\n` +
    `  Camera: ${payload.camera_name}\n` +
    `  Criticality: ${payload.criticality}\n` +
    `  Message: ${payload.message}`,
  )

  return { sent: payload.groups.length }
}
